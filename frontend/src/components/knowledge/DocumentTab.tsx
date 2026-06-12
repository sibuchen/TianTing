'use client';
 
import React, { useState } from 'react';
import { Popconfirm, Tooltip, message, Dropdown, Modal } from 'antd';
import { useTranslations } from 'next-intl';
import { knowledgeApi } from '@/lib/api';

interface Document {
  id: string;
  fileName: string;
  fileType: string;
  fileSize: number;
  vectorStatus: string;
  vectorProgress: number;
  totalChunks: number;
  processedChunks: number;
  createdAt: string;
}

const FALLBACK_DOCUMENTS: Document[] = [
  {
    id: 'doc-1',
    fileName: 'Refund Policy.pdf',
    fileType: 'pdf',
    fileSize: 2516582,
    vectorStatus: 'completed',
    vectorProgress: 100,
    totalChunks: 120,
    processedChunks: 120,
    createdAt: 'Oct 24, 10:30 AM',
  },
  {
    id: 'doc-2',
    fileName: 'Product FAQ.docx',
    fileType: 'docx',
    fileSize: 1153433,
    vectorStatus: 'processing',
    vectorProgress: 37.5,
    totalChunks: 120,
    processedChunks: 45,
    createdAt: 'Just now',
  },
  {
    id: 'doc-3',
    fileName: 'Store Intro.txt',
    fileType: 'txt',
    fileSize: 12288,
    vectorStatus: 'failed',
    vectorProgress: 0,
    totalChunks: 0,
    processedChunks: 0,
    createdAt: 'Oct 23, 14:15 PM',
  },
];

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function getFileIcon(fileType: string): string {
  if (fileType === 'pdf') return 'picture_as_pdf';
  if (fileType === 'docx' || fileType === 'doc') return 'description';
  return 'text_snippet';
}

interface DocumentTabProps {
  documents?: Document[];
  onRefresh?: () => void;
}

export default function DocumentTab({ documents: externalDocs, onRefresh }: DocumentTabProps) {
  const t = useTranslations('Knowledge.doc');
  const docs = externalDocs && externalDocs.length > 0 ? externalDocs : [];

  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [previewFileName, setPreviewFileName] = useState('');
  const [previewFileType, setPreviewFileType] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);

  const handlePreview = async (docId: string) => {
    try {
      setPreviewLoading(true);
      setPreviewOpen(true);
      const res: any = await knowledgeApi.previewDocument(docId);
      const data = res?.data ?? res;
      setPreviewContent(data?.content || '');
      setPreviewFileName(data?.fileName || '');
      setPreviewFileType(data?.fileType || '');
    } catch {
      message.error(t('previewFailed') || '预览失败');
      setPreviewOpen(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await knowledgeApi.deleteDocument(docId);
      message.success(t('deleteSuccess') || 'Deleted');
      onRefresh?.();
    } catch {
      message.error(t('deleteFailed') || 'Delete failed');
    }
  };

  const handleRetry = async (docId: string) => {
    try {
      await knowledgeApi.retryDocument(docId);
      message.success(t('retryStarted') || 'Retry started');
      onRefresh?.();
    } catch {
      message.error(t('retryFailed') || 'Retry failed');
    }
  };

  return (
    <div className="flex flex-col gap-md">
      {/* Toolbar */}
      <div className="flex justify-between items-center mb-md bg-card-bg p-3 rounded-xl border border-outline-variant shadow-soft">
        <div className="relative w-full max-w-md">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[20px]">search</span>
          <input 
            className="w-full pl-10 pr-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" 
            placeholder={t('search')} 
            type="text"
          />
        </div>
        <div className="flex items-center gap-2">
          <Tooltip title={t('filter')}>
            <button className="p-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low rounded-lg transition-colors border border-outline-variant">
              <span className="material-symbols-outlined text-[20px]">filter_list</span>
            </button>
          </Tooltip>
          <Tooltip title={t('sort')}>
            <button className="p-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low rounded-lg transition-colors border border-outline-variant">
              <span className="material-symbols-outlined text-[20px]">sort</span>
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Document Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-md">
        {docs.map((doc: any) => (
          <div 
            key={doc.id} 
            className="bg-card-bg rounded-[12px] border border-outline-variant p-md shadow-soft hover:-translate-y-[2px] hover:shadow-lg transition-all flex flex-col group relative overflow-hidden"
          >
            <div className={`absolute top-0 right-0 w-16 h-16 bg-${doc.vectorStatus === 'failed' ? 'error' : doc.vectorStatus === 'processing' || doc.vectorStatus === 'pending' ? 'info' : 'success'}/5 rounded-bl-[100%] -z-0`}></div>
            
            <div className="flex justify-between items-start mb-4 relative z-10">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center ${doc.vectorStatus === 'processing' || doc.vectorStatus === 'pending' ? 'text-info' : doc.vectorStatus === 'failed' ? 'text-outline' : 'text-primary'}`}>
                  <span className="material-symbols-outlined">{getFileIcon(doc.fileType)}</span>
                </div>
                <div>
                  <h3 className="font-label-md text-on-surface truncate max-w-[180px]" title={doc.fileName}>{doc.fileName}</h3>
                  <p className="font-body-sm text-on-surface-variant">{formatFileSize(doc.fileSize)}</p>
                </div>
              </div>
              <Dropdown
                menu={{
                  items: [
                    ...(doc.vectorStatus === 'completed' ? [{
                      key: 'preview',
                      label: t('preview'),
                      icon: <span className="material-symbols-outlined text-[16px]">visibility</span>,
                    }] : []),
                    ...(doc.vectorStatus === 'failed' ? [{
                      key: 'retry',
                      label: t('retry'),
                      icon: <span className="material-symbols-outlined text-[16px]">refresh</span>,
                    }] : []),
                    {
                      key: 'delete',
                      label: t('delete'),
                      danger: true,
                      icon: <span className="material-symbols-outlined text-[16px]">delete</span>,
                    },
                  ],
                  onClick: ({ key }) => {
                    if (key === 'delete') handleDelete(doc.id);
                    if (key === 'retry') handleRetry(doc.id);
                    if (key === 'preview') handlePreview(doc.id);
                  },
                }}
                trigger={['click']}
              >
                <button className="text-outline hover:text-on-surface transition-colors p-1">
                  <span className="material-symbols-outlined text-[20px]">more_vert</span>
                </button>
              </Dropdown>
            </div>

            <div className="mt-auto pt-4 border-t border-outline-variant flex flex-col gap-3">
              <div className="flex justify-between items-center">
                {doc.vectorStatus === 'completed' && (
                  <div className="flex items-center gap-1.5 text-success">
                    <span className="material-symbols-outlined filled text-[16px]">check_circle</span>
                    <span className="font-label-sm">{t('completed')}</span>
                  </div>
                )}
                {doc.vectorStatus === 'pending' && (
                  <div className="flex items-center gap-1.5 text-on-surface-variant">
                    <span className="material-symbols-outlined text-[16px]">schedule</span>
                    <span className="font-label-sm">{t('pending') || 'Pending'}</span>
                  </div>
                )}
                {doc.vectorStatus === 'processing' && (
                  <div className="flex items-center gap-1.5 text-info">
                    <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
                    <span className="font-label-sm">{t('processing')} {doc.processedChunks}/{doc.totalChunks}</span>
                  </div>
                )}
                {doc.vectorStatus === 'failed' && (
                  <div className="flex items-center gap-1.5 text-error">
                    <span className="material-symbols-outlined filled text-[16px]">error</span>
                    <span className="font-label-sm">{t('failed')}</span>
                  </div>
                )}
                <span className="font-body-sm text-outline">{doc.createdAt}</span>
              </div>

              {(doc.vectorStatus === 'pending' || doc.vectorStatus === 'processing') && (
                <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden">
                  <div className={`${doc.vectorStatus === 'pending' ? 'bg-on-surface-variant' : 'bg-info'} h-1.5 rounded-full transition-all duration-500`} style={{ width: `${doc.vectorProgress}%` }}></div>
                </div>
              )}

              <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                {doc.vectorStatus === 'completed' && (
                  <>
                    <button onClick={() => handlePreview(doc.id)} className="flex-1 bg-surface-container-low text-primary font-label-sm py-1.5 rounded-lg hover:bg-primary-container border border-transparent hover:border-primary/20 transition-all flex items-center justify-center gap-1">
                      <span className="material-symbols-outlined text-[16px]">visibility</span> {t('preview')}
                    </button>
                    <Popconfirm title={t('confirmDelete')} okText={t('yes')} cancelText={t('no')} onConfirm={() => handleDelete(doc.id)}>
                      <button className="px-3 bg-surface-container-lowest text-error font-label-sm py-1.5 rounded-lg hover:bg-error-container border border-outline-variant hover:border-error/20 transition-all flex items-center justify-center">
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                      </button>
                    </Popconfirm>
                  </>
                )}
                {doc.vectorStatus === 'pending' && (
                  <>
                    <button disabled className="flex-1 bg-surface-container-low text-primary font-label-sm py-1.5 rounded-lg opacity-50 cursor-not-allowed border border-transparent transition-all flex items-center justify-center gap-1">
                      <span className="material-symbols-outlined text-[16px]">visibility</span> {t('preview')}
                    </button>
                    <Popconfirm title={t('confirmDelete')} okText={t('yes')} cancelText={t('no')} onConfirm={() => handleDelete(doc.id)}>
                      <button className="px-3 bg-surface-container-lowest text-error font-label-sm py-1.5 rounded-lg hover:bg-error-container border border-outline-variant hover:border-error/20 transition-all flex items-center justify-center">
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                      </button>
                    </Popconfirm>
                  </>
                )}
                {doc.vectorStatus === 'processing' && (
                  <>
                    <button disabled className="flex-1 bg-surface-container-low text-primary font-label-sm py-1.5 rounded-lg opacity-50 cursor-not-allowed border border-transparent transition-all flex items-center justify-center gap-1">
                      <span className="material-symbols-outlined text-[16px]">visibility</span> {t('preview')}
                    </button>
                    <Popconfirm title={t('confirmCancel')} okText={t('yes')} cancelText={t('no')} onConfirm={() => handleDelete(doc.id)}>
                      <button className="px-3 bg-surface-container-lowest text-error font-label-sm py-1.5 rounded-lg hover:bg-error-container border border-border-light hover:border-error-container transition-all flex items-center justify-center">
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                      </button>
                    </Popconfirm>
                  </>
                )}
                {doc.vectorStatus === 'failed' && (
                  <>
                    <button onClick={() => handleRetry(doc.id)} className="flex-1 bg-surface-container-low text-primary font-label-sm py-1.5 rounded-lg hover:bg-primary-light border border-transparent hover:border-primary-light transition-all flex items-center justify-center gap-1">
                      <span className="material-symbols-outlined text-[16px]">refresh</span> {t('retry')}
                    </button>
                    <Popconfirm title={t('confirmDelete')} okText={t('yes')} cancelText={t('no')} onConfirm={() => handleDelete(doc.id)}>
                      <button className="px-3 bg-surface-container-lowest text-error font-label-sm py-1.5 rounded-lg hover:bg-error-container border border-border-light hover:border-error-container transition-all flex items-center justify-center">
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                      </button>
                    </Popconfirm>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{previewFileName || t('preview')}</span>}
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={null}
        centered
        width={720}
        className="custom-modal"
      >
        {previewLoading ? (
          <div className="flex items-center justify-center py-12">
            <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
          </div>
        ) : (
          <div className="mt-4 max-h-[60vh] overflow-auto">
            <pre className="whitespace-pre-wrap font-body-sm text-body-sm text-on-surface bg-surface-container-lowest p-lg rounded-lg border border-outline-variant">
              {previewContent || t('noContent') || 'No content available'}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  );
}
