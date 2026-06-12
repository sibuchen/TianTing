'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { App, Modal, Form, Input, Popconfirm } from 'antd';
import { apiKeysApi } from '@/lib/api';

interface ApiKeyConfig {
  id: string;
  name: string;
  description: string;
  baseUrl: string;
  modelId: string;
  apiKey: string;
  status: 'normal' | 'error';
  boundAgents: string[];
  errorMsg?: string;
}

export default function ApiKeysPage() {
  const { message } = App.useApp();
  const t = useTranslations('ApiKeys');
  const [configs, setConfigs] = useState<ApiKeyConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ApiKeyConfig | null>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [baseUrlPreview, setBaseUrlPreview] = useState('');

  const normalizeChatUrl = (url: string): string => {
    const trimmed = url.replace(/\/+$/, '');
    if (!trimmed) return '';
    if (trimmed.endsWith('/chat/completions')) return trimmed;
    return `${trimmed}/chat/completions`;
  };

  const fetchConfigs = useCallback(() => {
    setLoading(true);
    apiKeysApi.list()
      .then((res: any) => {
        const data = res?.data ?? res ?? [];
        setConfigs(Array.isArray(data) ? data : data?.items ?? []);
      })
      .catch(() => {
        setConfigs([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchConfigs();
  }, [fetchConfigs]);

  const toggleKeyVisibility = (id: string) => {
    setVisibleKeys(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleAdd = () => {
    setEditingConfig(null);
    form.resetFields();
    setBaseUrlPreview('');
    setModalOpen(true);
  };

  const handleEdit = (config: ApiKeyConfig) => {
    setEditingConfig(config);
    form.setFieldsValue({
      name: config.name,
      baseUrl: config.baseUrl,
      modelId: config.modelId,
      apiKey: config.apiKey,
    });
    setBaseUrlPreview(normalizeChatUrl(config.baseUrl));
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      if (editingConfig) {
        await apiKeysApi.update(editingConfig.id, values);
        message.success(t('updateSuccess') || 'Updated');
      } else {
        await apiKeysApi.create(values);
        message.success(t('createSuccess') || 'Created');
      }
      setModalOpen(false);
      fetchConfigs();
    } catch {
      message.error(t('saveFailed') || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiKeysApi.delete(id);
      message.success(t('deleteSuccess') || 'Deleted');
      fetchConfigs();
    } catch (error: any) {
      const status = error?.response?.status;
      const data = error?.response?.data;
      if (status === 400 && data?.code === 80005) {
        message.error(t('deleteInUse') || '该密钥已被智能体使用，请先解绑后再删除');
      } else {
        message.error(t('deleteFailed') || 'Delete failed');
      }
    }
  };

  const handleTest = async (id: string) => {
    try {
      setTestingId(id);
      const res: any = await apiKeysApi.test(id);
      const data = res?.data;
      if (data?.status === 'normal' || data?.status === 'online' || data?.success) {
        message.success(t('testSuccess') || 'Connection successful');
      } else {
        message.warning(t('testWarning') || 'Connection issue detected');
      }
      fetchConfigs();
    } catch (err: any) {
      const serverMsg = err?.response?.data?.message || err?.message || '';
      message.error(serverMsg || t('testFailed') || 'Connection failed');
    } finally {
      setTestingId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-on-surface">{t('title')}</h2>
            <p className="text-sm text-on-surface-variant mt-1">{t('subtitle')}</p>
          </div>
          <button
            onClick={handleAdd}
            className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-primary-container hover:scale-[1.02] transition-all shadow-sm"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
            {t('addModel')}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {loading ? (
            <div className="col-span-full flex items-center justify-center py-20">
              <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
            </div>
          ) : (
          configs.map((config) => (
            <div
              key={config.id}
              className={`bg-card-bg rounded-xl shadow-soft p-lg hover:shadow-lg transition-all duration-300 border flex flex-col h-full ${config.status === 'error' ? 'border-error/10 bg-error-container/5' : 'border-outline-variant'
                }`}
            >
              <div className="flex justify-between items-start mb-lg">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${config.status === 'error' ? 'bg-error/5' : 'bg-primary-light'
                    }`}>
                    <span className={`material-symbols-outlined text-2xl ${config.status === 'error' ? 'text-error' : 'text-primary'
                      }`}>
                      {config.status === 'error' ? 'smart_toy' : 'psychology'}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-h3 text-h3 text-on-surface font-semibold tracking-tight">{config.name}</h3>
                    <p className="font-label-sm text-label-sm text-on-surface-variant mt-0.5">{t(config.description)}</p>
                  </div>
                </div>
                <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border ${config.status === 'error'
                  ? 'border-error/20 bg-error/5'
                  : 'border-success/20 bg-success/5'
                  }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${config.status === 'error' ? 'bg-error animate-pulse' : 'bg-success'
                    }`}></span>
                  <span className={`font-label-sm text-label-sm font-medium ${config.status === 'error' ? 'text-error' : 'text-success'
                    }`}>{t(config.status)}</span>
                </div>
              </div>

              <div className="flex flex-col gap-4 mb-lg">
                <div className="grid grid-cols-[80px_1fr] gap-x-3 items-center">
                  <div className="text-sm font-bold text-on-surface-variant/80 uppercase tracking-tight">{t('baseUrl')}</div>
                  <div className="font-code text-code text-on-surface bg-surface-bg px-3 h-10 flex items-center rounded-lg border border-outline-variant min-w-0">
                    <span className="truncate">{config.baseUrl}</span>
                  </div>
                </div>
                <div className="grid grid-cols-[80px_1fr] gap-x-3 items-center">
                  <div className="text-sm font-bold text-on-surface-variant/80 uppercase tracking-tight">{t('modelId')}</div>
                  <div className="font-code text-code text-on-surface bg-surface-bg px-3 h-10 flex items-center rounded-lg border border-outline-variant min-w-0">
                    <span className="truncate">{config.modelId}</span>
                  </div>
                </div>
                <div className="grid grid-cols-[80px_1fr] gap-x-3 items-center">
                  <div className="text-sm font-bold text-on-surface-variant/80 uppercase tracking-tight">{t('apiKey')}</div>
                  <div className={`flex items-center gap-2 px-3 h-10 rounded-lg border min-w-0 ${config.status === 'error' ? 'bg-card-bg border-error/20' : 'bg-surface-bg border-outline-variant'
                    }`}>
                    <div className={`font-code text-code text-on-surface flex-1 flex items-center gap-1 min-w-0 ${config.status === 'error' ? 'opacity-70' : ''
                      }`}>
                      {visibleKeys[config.id] ? (
                        <span className="truncate">{config.apiKey}</span>
                      ) : (
                        <div className="flex items-center overflow-hidden">
                          <span className="tracking-[0.2em] font-bold opacity-60 text-lg leading-none pt-1">••••••••••••••••</span>
                          <span className="ml-1 flex-shrink-0">{config.apiKey?.slice(-4)}</span>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => toggleKeyVisibility(config.id)}
                      className="text-on-surface-variant hover:text-primary transition-colors p-1 rounded hover:bg-card-bg flex items-center justify-center shadow-sm"
                    >
                      <span className="material-symbols-outlined text-[18px]">
                        {visibleKeys[config.id] ? 'visibility' : 'visibility_off'}
                      </span>
                    </button>
                  </div>
                </div>
              </div>

              {config.errorMsg && (
                <div className="mb-lg p-4 bg-error/[0.03] border border-error/10 rounded-xl flex items-start gap-3">
                  <span className="material-symbols-outlined text-error text-xl">report</span>
                  <p className="font-body-sm text-body-sm text-on-surface leading-relaxed">{t(config.errorMsg)}</p>
                </div>
              )}

              {config.boundAgents && config.boundAgents.length > 0 && (
                <div className="mb-lg">
                  <div className="font-label-sm text-label-sm text-on-surface-variant mb-2">{t('boundAgents')}</div>
                  <div className="flex flex-wrap gap-2">
                    {config.boundAgents.map((agent, idx) => (
                      <span
                        key={idx}
                        className={`px-3 py-1 rounded-full font-label-sm text-label-sm border ${idx === 0 && config.status !== 'error'
                          ? 'bg-primary/5 text-primary border-primary/10'
                          : 'bg-surface-bg text-on-surface-variant border-outline-variant'
                          }`}
                      >
                        {t(agent)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3 mt-auto pt-lg">
                <button
                  onClick={() => handleEdit(config)}
                  className="px-5 py-2 font-label-md text-label-md text-on-surface hover:text-primary hover:border-primary/50 rounded-lg transition-all border border-outline-variant bg-card-bg"
                >
                  {t('edit')}
                </button>
                <button
                  onClick={() => handleTest(config.id)}
                  disabled={testingId === config.id}
                  className="px-5 py-2 font-label-md text-label-md text-primary hover:bg-primary/5 rounded-lg transition-all border border-primary/30"
                >
                  {testingId === config.id ? (
                    <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                  ) : t('test') || 'Test'}
                </button>
                <Popconfirm
                  title={t('confirmDelete') || 'Are you sure to delete this?'}
                  onConfirm={() => handleDelete(config.id)}
                  okText={t('yes') || 'Yes'}
                  cancelText={t('no') || 'No'}
                >
                  <button className="px-5 py-2 font-label-md text-label-md text-error hover:bg-error/5 rounded-lg transition-all border border-transparent">
                    {t('delete')}
                  </button>
                </Popconfirm>
              </div>
            </div>
          )))}
        </div>
      </div>

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{editingConfig ? t('editModel') || 'Edit Model' : t('addModel')}</span>}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        confirmLoading={saving}
        okText={t('save') || 'Save'}
        cancelText={t('cancel') || 'Cancel'}
        centered
        width={520}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item
            name="name"
            label={t('modelName') || 'Model Name'}
            rules={[{ required: true, message: t('nameRequired') || 'Please enter model name' }]}
          >
            <Input className="rounded-lg" />
          </Form.Item>
          <Form.Item
            name="baseUrl"
            label={t('baseUrl')}
            rules={[{ required: true, message: t('baseUrlRequired') || 'Please enter base URL' }]}
          >
            <Input
              className="rounded-lg font-code"
              placeholder="https://api.openai.com/v1"
              onChange={(e) => setBaseUrlPreview(normalizeChatUrl(e.target.value))}
            />
          </Form.Item>
          {baseUrlPreview && (
            <div className="mt-[-16px] mb-4 px-3 py-2 bg-surface-container-low rounded-lg border border-outline-variant">
              <span className="text-xs text-on-surface-variant">预览：</span>
              <span className="font-code text-xs text-primary font-medium">{baseUrlPreview}</span>
            </div>
          )}
          <Form.Item
            name="modelId"
            label={t('modelId')}
            rules={[{ required: true, message: t('modelIdRequired') || 'Please enter model ID' }]}
          >
            <Input className="rounded-lg font-code" placeholder="gpt-4" />
          </Form.Item>
          <Form.Item
            name="apiKey"
            label={t('apiKey')}
            rules={[{ required: !editingConfig, message: t('apiKeyRequired') || 'Please enter API key' }]}
          >
            <Input.Password className="rounded-lg font-code" placeholder={editingConfig ? 'Leave empty to keep current key' : 'sk-...'} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
