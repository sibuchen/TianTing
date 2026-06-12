'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { useTranslations } from 'next-intl';
import { App } from 'antd';
import { knowledgeApi, agentsApi } from '@/lib/api';

interface QAItem {
  id: string;
  question: string;
  answer: string;
}

export interface QATabHandle {
  save: () => Promise<boolean>;
  isDirty: () => boolean;
}

const QATab = forwardRef<QATabHandle, { agentId: string, agentData?: Record<string, any> }>(function QATab({ agentId, agentData }, ref) {
  const { message } = App.useApp();
  const t = useTranslations('AgentEdit.qa');
  const [qaList, setQaList] = useState<QAItem[]>([]);
  const [associatedIds, setAssociatedIds] = useState<Set<string>>(new Set());
  const [originalAssociatedIds, setOriginalAssociatedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const qaRes = await knowledgeApi.listQA();
        const rawQA = qaRes as unknown as Record<string, unknown>;
        const items: QAItem[] = Array.isArray(qaRes)
          ? qaRes
          : Array.isArray((rawQA?.data as Record<string, unknown>)?.items)
            ? (rawQA!.data as Record<string, unknown>).items as QAItem[]
            : Array.isArray(rawQA?.data)
              ? rawQA!.data as QAItem[]
              : Array.isArray(rawQA?.items)
                ? rawQA!.items as QAItem[]
                : [];
        setQaList(items);

        let linkedIds: string[] = [];
        if (agentData) {
          linkedIds = Array.isArray(agentData?.knowledgeQaList)
            ? (agentData.knowledgeQaList as Array<Record<string, unknown>>).map(
                (q: Record<string, unknown>) => (q.id || q.qaId || q.qa_id) as string
              )
            : Array.isArray(agentData?.knowledge_qa_list)
            ? (agentData.knowledge_qa_list as Array<Record<string, unknown>>).map(
                (q: Record<string, unknown>) => (q.id || q.qaId || q.qa_id) as string
              )
            : [];
        }
        const idSet = new Set(linkedIds);
        setAssociatedIds(idSet);
        setOriginalAssociatedIds(new Set(idSet));
      } catch {
        setQaList([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [agentData]);

  const toggleQA = (qaId: string) => {
    setAssociatedIds(prev => {
      const next = new Set(prev);
      if (next.has(qaId)) {
        next.delete(qaId);
      } else {
        next.add(qaId);
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
      for (const qaId of toAdd) {
        await agentsApi.addKnowledgeQA(agentId, qaId);
      }
      for (const qaId of toRemove) {
        await agentsApi.removeKnowledgeQA(agentId, qaId);
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
              <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">{t('question')}</th>
              <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">{t('answer')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {qaList.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-md py-12 text-center text-on-surface-variant font-body-sm text-body-sm">
                  {t('noQA')}
                </td>
              </tr>
            ) : (
              qaList.map((qa) => {
                const isAssociated = associatedIds.has(qa.id);
                return (
                  <tr key={qa.id} className="hover:bg-surface-container transition-colors group">
                    <td className="px-md py-4">
                      <input
                        type="checkbox"
                        checked={isAssociated}
                        onChange={() => toggleQA(qa.id)}
                        className="w-4 h-4 rounded border-outline-variant text-primary focus:ring-primary-light accent-primary cursor-pointer"
                      />
                    </td>
                    <td className="px-md py-4">
                      <span className="font-label-md text-label-md text-on-surface font-medium">{qa.question}</span>
                    </td>
                    <td className="px-md py-4">
                      <span className="font-body-sm text-body-sm text-on-surface-variant line-clamp-2">{qa.answer}</span>
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

export default QATab;
