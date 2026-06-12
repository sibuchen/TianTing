'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Form, Input, Button, Tooltip, Popconfirm, App } from 'antd';
import { useTranslations } from 'next-intl';
import { knowledgeApi } from '@/lib/api';

const { TextArea } = Input;

interface QAItem {
  id: string;
  question: string;
  answer: string;
  created_at?: string;
}

export default function QATab() {
  const { message } = App.useApp();
  const t = useTranslations('Knowledge.qa');
  const [qaList, setQaList] = useState<QAItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingQA, setEditingQA] = useState<QAItem | null>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const pageSize = 10;

  const fetchQAList = useCallback(() => {
    setLoading(true);
    knowledgeApi.listQA({ search: searchText || undefined, page, page_size: pageSize })
      .then((res: any) => {
        const data = res?.data ?? res;
        setQaList(data?.items ?? (Array.isArray(data) ? data : []));
        setTotal(data?.total ?? 0);
        setTotalPages(data?.totalPages ?? data?.total_pages ?? 0);
      })
      .catch(() => {
        setQaList([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [searchText, page]);

  useEffect(() => {
    fetchQAList();
  }, [fetchQAList]);

  const toggleExpand = (id: string) => {
    setExpandedRows(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleAdd = () => {
    setEditingQA(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const handleEdit = (qa: QAItem) => {
    setEditingQA(qa);
    form.setFieldsValue({ question: qa.question, answer: qa.answer });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editingQA) {
        await knowledgeApi.updateQA(editingQA.id, values);
        message.success(t('updateSuccess') || 'Updated');
      } else {
        await knowledgeApi.createQA(values);
        message.success(t('createSuccess') || 'Created');
      }
      setIsModalOpen(false);
      fetchQAList();
    } catch {
      message.error(t('saveFailed') || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (qaId: string) => {
    try {
      await knowledgeApi.deleteQA(qaId);
      message.success(t('deleteSuccess') || 'Deleted');
      fetchQAList();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      const msg = error?.response?.data?.message;
      message.error(msg || detail || t('deleteFailed') || 'Delete failed');
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchQAList();
  };

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div className="flex-1 flex flex-col gap-md">
      <div className="flex justify-between items-center">
        <div className="relative w-80">
          <span className="material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-outline text-lg">search</span>
          <input
            className="w-full pl-10 pr-4 py-2 border border-outline-variant rounded-[8px] font-body-md text-body-md focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary text-on-surface bg-surface-container-lowest transition-shadow"
            placeholder={t('search')}
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <button
          onClick={handleAdd}
          className="bg-primary text-on-primary px-4 py-2 rounded-[8px] font-label-md text-label-md flex items-center gap-2 hover:scale-[1.02] hover:shadow-md transition-all active:scale-95 shadow-sm"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          {t('add')}
        </button>
      </div>

      <div className="flex-1 overflow-x-auto rounded-[8px] border border-outline-variant bg-card-bg shadow-soft">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
          </div>
        ) : qaList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-on-surface-variant">
            <span className="material-symbols-outlined text-4xl mb-2">quiz</span>
            <p className="font-body-md text-body-md">{t('noData') || 'No Q&A pairs found'}</p>
          </div>
        ) : (
        <table className="w-full text-left border-collapse">
          <thead className="bg-surface-container-low border-b border-outline-variant font-label-md text-label-md text-on-surface">
            <tr>
              <th className="px-md py-3 font-medium">{t('question')}</th>
              <th className="px-md py-3 font-medium w-1/2">{t('answer')}</th>
              <th className="px-md py-3 font-medium">{t('createdTime')}</th>
              <th className="px-md py-3 font-medium text-right">{t('action')}</th>
            </tr>
          </thead>
          <tbody className="font-body-sm text-body-sm text-on-surface-variant divide-y divide-outline-variant">
            {qaList.map((qa) => (
              <tr key={qa.id} className="hover:bg-surface-container-lowest transition-colors group">
                <td className="px-md py-4 align-top font-medium text-on-surface w-1/4">
                  {qa.question}
                </td>
                <td className="px-md py-4 align-top">
                  <div className={expandedRows[qa.id] ? '' : 'line-clamp-2'}>
                    {qa.answer}
                  </div>
                  <button
                    onClick={() => toggleExpand(qa.id)}
                    className="text-primary hover:underline mt-1 font-medium text-xs transition-colors"
                  >
                    {expandedRows[qa.id] ? t('showLess') : t('showMore')}
                  </button>
                </td>
                <td className="px-md py-4 align-top whitespace-nowrap">
                  {qa.created_at ? new Date(qa.created_at).toLocaleString() : '-'}
                </td>
                <td className="px-md py-4 align-top text-right">
                  <div className="flex justify-end gap-2">
                    <Tooltip title={t('edit')}>
                      <button
                        onClick={() => handleEdit(qa)}
                        className="p-1 text-info hover:bg-primary/10 rounded transition-colors"
                      >
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </button>
                    </Tooltip>
                    <Popconfirm
                      title={t('confirmDelete')}
                      okText={t('yes')}
                      cancelText={t('no')}
                      onConfirm={() => handleDelete(qa.id)}
                    >
                      <button className="p-1 text-error hover:bg-error-container rounded transition-colors" title={t('delete')}>
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </Popconfirm>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )}
      </div>

      {total > 0 && (
        <div className="flex justify-between items-center pt-sm text-on-surface-variant font-body-sm text-body-sm">
          <span>{t('showing', { start, end, total })}</span>
          <div className="flex gap-1">
            <button
              className="px-2 py-1 border border-outline-variant rounded hover:bg-surface-container-low transition-colors disabled:opacity-50"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >Prev</button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).slice(Math.max(0, page - 3), page + 2).map((p) => (
              <button
                key={p}
                className={`px-2 py-1 border rounded transition-colors ${p === page ? 'border-primary bg-primary text-on-primary' : 'border-outline-variant hover:bg-surface-container-low'}`}
                onClick={() => setPage(p)}
              >{p}</button>
            ))}
            <button
              className="px-2 py-1 border border-outline-variant rounded hover:bg-surface-container-low transition-colors disabled:opacity-50"
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >Next</button>
          </div>
        </div>
      )}

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{editingQA ? t('editTitle') || 'Edit Q&A' : t('modalTitle')}</span>}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        centered
        width={600}
        className="custom-modal"
      >
        <Form form={form} layout="vertical" className="mt-6">
          <Form.Item
            name="question"
            label={<span className="font-label-md text-on-surface">{t('question')}</span>}
            rules={[{ required: true, message: t('questionRequired') || 'Question is required' }]}
            className="mb-6"
          >
            <TextArea
              rows={3}
              placeholder={t('questionPlaceholder')}
              className="rounded-lg border-outline-variant focus:ring-primary/20"
            />
          </Form.Item>
          <Form.Item
            name="answer"
            label={<span className="font-label-md text-on-surface">{t('answer')}</span>}
            rules={[{ required: true, message: t('answerRequired') || 'Answer is required' }]}
          >
            <TextArea
              rows={6}
              placeholder={t('answerPlaceholder')}
              className="rounded-lg border-outline-variant focus:ring-primary/20"
            />
          </Form.Item>

          <div className="flex gap-3 mt-10">
            <Button
              block
              className="h-11 rounded-lg border-outline-variant text-on-surface font-label-md"
              onClick={() => setIsModalOpen(false)}
            >
              {t('cancel')}
            </Button>
            <Button
              type="primary"
              block
              className="h-11 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-label-md border-none shadow-sm"
              loading={saving}
              onClick={handleSave}
            >
              {t('save')}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
