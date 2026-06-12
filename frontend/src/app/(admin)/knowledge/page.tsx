'use client';
 
import React, { useState, useEffect, useRef, useCallback } from 'react';
import DocumentTab from '@/components/knowledge/DocumentTab';
import QATab from '@/components/knowledge/QATab';
import { useTranslations } from 'next-intl';
import { SlidingSwitch } from '@/components/ui/SlidingSwitch';
import { knowledgeApi } from '@/lib/api';

export default function KnowledgePage() {
  const t = useTranslations('Knowledge');
  const [activeTab, setActiveTab] = useState('doc');
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDocuments = useCallback(() => {
    knowledgeApi.listDocuments()
      .then((res: any) => {
        const data = res?.data ?? res;
        const items = data?.items ?? (Array.isArray(data) ? data : []);
        setDocuments(items);
      })
      .catch(() => {
        setDocuments([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const hasPendingDocs = useCallback(() => {
    return documents.some(
      (doc: any) => doc.vectorStatus === 'pending' || doc.vectorStatus === 'processing'
    );
  }, [documents]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    if (hasPendingDocs()) {
      pollingRef.current = setInterval(fetchDocuments, 3000);
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [documents, fetchDocuments, hasPendingDocs]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      await knowledgeApi.uploadDocument(formData);
      fetchDocuments();
    } catch {
      // handle error silently
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'doc':
        return <DocumentTab documents={documents} onRefresh={fetchDocuments} />;
      case 'qa':
        return <QATab />;
      default:
        return <DocumentTab documents={documents} onRefresh={() => {}} />;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="space-y-8">
        {/* Page Header Area */}
        <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-on-surface">{t('title')}</h2>
          <p className="text-sm text-on-surface-variant mt-1">{t('subtitle')}</p>
        </div>
        <div className="flex items-center gap-3">
          {activeTab === 'doc' && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md,.doc,.docx,.csv"
                className="hidden"
                onChange={handleFileChange}
              />
              <button
                onClick={handleUploadClick}
                disabled={uploading}
                className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-primary-container hover:scale-[1.02] transition-all shadow-sm disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[20px]">{uploading ? 'progress_activity' : 'add'}</span>
                {uploading ? t('uploading') || 'Uploading...' : t('uploadDoc')}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <SlidingSwitch 
        value={activeTab}
        onChange={setActiveTab}
        options={[
          { label: t('docTab'), value: 'doc' },
          { label: t('qaTab'), value: 'qa' },
        ]}
      />

      {/* Content Area */}
      <div className="animate-in fade-in duration-500">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
          </div>
        ) : (
          renderTabContent()
        )}
      </div>
      </div>
    </div>
  );
}

