'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { useTranslations } from 'next-intl';
import { App } from 'antd';
import { knowledgeApi, agentsApi } from '@/lib/api';

interface Document {
  id: string;
  filename: string;
  original_filename?: string;
  vector_status?: string;
  status?: string;
}

export interface KnowledgeTabHandle {
  save: () => Promise<boolean>;
  isDirty: () => boolean;
}

const KnowledgeTab = forwardRef<KnowledgeTabHandle, { agentId: string, agentData?: Record<string, any> }>(function KnowledgeTab({ agentId, agentData }, ref) {
  const { message } = App.useApp();
  const t = useTranslations('AgentEdit.knowledge');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [associatedIds, setAssociatedIds] = useState<Set<string>>(new Set());
  const [originalAssociatedIds, setOriginalAssociatedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const docsRes = await knowledgeApi.listDocuments();
        const rawDocs = docsRes as unknown as Record<string, unknown>;
        const docList: Document[] = Array.isArray(docsRes)
          ? docsRes
          : Array.isArray((rawDocs?.data as Record<string, unknown>)?.items)
            ? (rawDocs!.data as Record<string, unknown>).items as Document[]
            : Array.isArray(rawDocs?.data)
              ? rawDocs!.data as Document[]
              : Array.isArray(rawDocs?.items)
                ? rawDocs!.items as Document[]
                : [];
        setDocuments(docList);

        let linkedIds: string[] = [];
        if (agentData) {
          linkedIds = Array.isArray(agentData?.knowledgeDocuments)
            ? (agentData.knowledgeDocuments as Array<Record<string, unknown>>).map(
                (d: Record<string, unknown>) => (d.id || d.documentId || d.document_id) as string
              )
            : Array.isArray(agentData?.knowledge_documents)
            ? (agentData.knowledge_documents as Array<Record<string, unknown>>).map(
                (d: Record<string, unknown>) => (d.id || d.documentId || d.document_id) as string
              )
            : [];
        }
        const idSet = new Set(linkedIds);
        setAssociatedIds(idSet);
        setOriginalAssociatedIds(new Set(idSet));
      } catch {
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [agentData]);

  const toggleDocument = (docId: string) => {
    setAssociatedIds(prev => {
      const next = new Set(prev);
      if (next.has(docId)) {
        next.delete(docId);
      } else {
        next.add(docId);
      }
      return next;
    });
  };

  const handleSave = async (): Promise<boolean> => {
    if (!agentId) return false;
    const toAdd = [...associatedIds].filter(id => !originalAssociatedIds.has(id));
    const toRemove = [...originalAssociatedIds].filter(id => !associatedIds.has(id));
    if (toAdd.length === 0 && toRemove.length === 0) return true;
    try {
      for (const docId of toAdd) {
        await agentsApi.addKnowledgeDocument(agentId, docId);
      }
      for (const docId of toRemove) {
        await agentsApi.removeKnowledgeDocument(agentId, docId);
      }
      setOriginalAssociatedIds(new Set(associatedIds));
      message.success(t('saveSuccess'));
      return true;
    } catch {
      message.error(t('saveFailed'));
      return false;
    }
  };

  useImperativeHandle(ref, () => ({
    save: handleSave,
    isDirty: () => {
      const toAdd = [...associatedIds].filter(id => !originalAssociatedIds.has(id));
      const toRemove = [...originalAssociatedIds].filter(id => !associatedIds.has(id));
      return toAdd.length > 0 || toRemove.length > 0;
    },
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-lg">
      <div>
        <h2 className="font-h2 text-h2 text-on-surface">{t('title')}</h2>
        <p className="font-body-md text-body-md text-on-surface-variant mt-xs">{t('desc')}</p>
      </div>

      <div className="bg-card-bg rounded-xl border border-outline-variant shadow-soft overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-outline-variant bg-surface-container-lowest">
              <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold w-12"></th>
              <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">{t('docName')}</th>
              <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold w-1/4">{t('vectorStatus')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {documents.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-md py-12 text-center text-on-surface-variant font-body-sm text-body-sm">
                  {t('noDocuments')}
                </td>
              </tr>
            ) : (
              documents.map((doc) => {
                const isAssociated = associatedIds.has(doc.id);
                const status = doc.vector_status || doc.status || '-';
                return (
                  <tr key={doc.id} className="hover:bg-surface-container transition-colors group">
                    <td className="px-md py-4">
                      <input
                        type="checkbox"
                        checked={isAssociated}
                        onChange={() => toggleDocument(doc.id)}
                        className="w-4 h-4 rounded border-outline-variant text-primary focus:ring-primary-light accent-primary cursor-pointer"
                      />
                    </td>
                    <td className="px-md py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-on-surface-variant border border-transparent group-hover:border-outline-variant">
                          <span className="material-symbols-outlined">description</span>
                        </div>
                        <span className="font-label-md text-label-md text-on-surface font-medium">
                          {doc.original_filename || doc.filename}
                        </span>
                      </div>
                    </td>
                    <td className="px-md py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-sm text-label-sm border ${
                        status === 'completed'
                          ? 'bg-surface-container-low text-success border-success/20'
                          : status === 'processing'
                          ? 'bg-surface-container-low text-warning border-warning/20'
                          : status === 'failed'
                          ? 'bg-error-container/30 text-error border-error/20'
                          : 'bg-surface-container-low text-on-surface-variant border-outline-variant'
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${
                          status === 'completed' ? 'bg-success' : status === 'processing' ? 'bg-warning' : status === 'failed' ? 'bg-error' : 'bg-on-surface-variant'
                        }`}></span>
                        {status === 'completed' ? 'Completed' : status === 'processing' ? 'Processing' : status === 'failed' ? 'Failed' : status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
});

export default KnowledgeTab;
