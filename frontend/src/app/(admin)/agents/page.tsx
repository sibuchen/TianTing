'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { App, Modal, Form, Input, Select, Popconfirm } from 'antd';
import { agentsApi } from '@/lib/api';

const { TextArea } = Input;

export default function AgentsPage() {
  const router = useRouter();
  const { message } = App.useApp();
  const t = useTranslations('Agents');
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const fetchAgents = useCallback(() => {
    setLoading(true);
    agentsApi.list()
      .then((data: any) => {
        const list = Array.isArray(data) ? data : data?.items ?? data?.data ?? [];
        setAgents(list);
      })
      .catch(() => {
        setAgents([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const handleCreate = () => {
    form.resetFields();
    setCreateOpen(true);
  };

  const handleCreateSubmit = async () => {
    try {
      const values = await form.validateFields();
      setCreating(true);
      await agentsApi.create(values);
      message.success(t('createSuccess') || 'Agent created');
      setCreateOpen(false);
      fetchAgents();
    } catch {
      message.error(t('createFailed') || 'Create failed');
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (agentId: string, currentEnabled: boolean) => {
    try {
      await agentsApi.toggle(agentId, !currentEnabled);
      message.success(t('toggleSuccess') || 'Status updated');
      fetchAgents();
    } catch {
      message.error(t('toggleFailed') || 'Toggle failed');
    }
  };

  const handleDelete = async (agentId: string) => {
    try {
      await agentsApi.delete(agentId);
      message.success(t('deleteSuccess') || 'Agent deleted');
      fetchAgents();
    } catch {
      message.error(t('deleteFailed') || 'Delete failed');
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
            onClick={handleCreate}
            className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-primary-container hover:scale-[1.02] transition-all shadow-sm"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
            {t('createAgent')}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            <div className="col-span-full text-center py-12 text-on-surface-variant">
              <span className="material-symbols-outlined text-[40px] animate-spin">progress_activity</span>
              <p className="mt-2 text-sm">{t('loading') ?? 'Loading...'}</p>
            </div>
          ) : agents.length === 0 ? (
            <div className="col-span-full text-center py-12 text-on-surface-variant">
              <span className="material-symbols-outlined text-[40px]">smart_toy</span>
              <p className="mt-2 text-sm">{t('noAgents') || 'No agents found'}</p>
            </div>
          ) : (
            agents.map((agent) => (
              <div key={agent.id} className="bg-card-bg rounded-[12px] p-6 shadow-soft hover:-translate-y-[2px] hover:shadow-lg transition-all duration-300 border border-outline-variant flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: agent.iconColor ? `${agent.iconColor}20` : undefined, color: agent.iconColor }}>
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>{agent.icon || 'smart_toy'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 border ${agent.isEnabled || agent.is_enabled ? 'bg-secondary-fixed text-on-secondary-fixed border-secondary-fixed-dim' : 'bg-surface-variant text-on-surface-variant border-outline-variant'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${agent.isEnabled || agent.is_enabled ? 'bg-success' : 'bg-on-surface-variant'}`}></span>
                      {(agent.isEnabled || agent.is_enabled) ? t('enabled') : t('disabled')}
                    </span>
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-on-surface mb-2">{agent.name}</h3>
                <p className="text-xs text-on-surface-variant mb-6 flex-1">{agent.description}</p>
                <div className="bg-surface-container-low rounded-lg p-3 mb-6 space-y-2 border border-outline-variant">
                  <div className="flex justify-between text-[13px] font-mono text-on-surface-variant">
                    <span>{t('model')}:</span>
                    <span className="text-on-surface">{agent.modelConfigId || agent.model_config_id || '-'}</span>
                  </div>
                  <div className="flex justify-between text-[13px] font-mono text-on-surface-variant">
                    <span>{t('skills')}:</span>
                    <span className="text-on-surface">{agent.skillsCount ?? agent.skills_count ?? 0}</span>
                  </div>
                  <div className="flex justify-between text-[13px] font-mono text-on-surface-variant">
                    <span>{t('tools')}:</span>
                    <span className="text-on-surface">{agent.toolsCount ?? agent.tools_count ?? 0}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-4 mt-auto">
                  <div className="flex items-center gap-2">
                    <button
                      className="text-primary hover:text-primary-container text-sm font-medium flex items-center gap-1 transition-colors"
                      onClick={() => router.push('/agents/' + agent.id)}
                    >
                      <span className="material-symbols-outlined text-[18px]">edit</span>
                      {t('edit')}
                    </button>
                    <Popconfirm
                      title={t('confirmDelete') || 'Delete this agent?'}
                      onConfirm={() => handleDelete(agent.id)}
                      okText={t('yes') || 'Yes'}
                      cancelText={t('no') || 'No'}
                    >
                      <button className="text-error hover:text-error-container text-sm font-medium flex items-center gap-1 transition-colors">
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </Popconfirm>
                  </div>
                  <button
                    onClick={() => handleToggle(agent.id, agent.isEnabled || agent.is_enabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${(agent.isEnabled || agent.is_enabled) ? 'bg-success' : 'bg-surface-variant'}`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-surface-container-lowest transition-transform ${(agent.isEnabled || agent.is_enabled) ? 'translate-x-6' : 'translate-x-1'}`}></span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{t('createAgent')}</span>}
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreateSubmit}
        confirmLoading={creating}
        okText={t('create') || 'Create'}
        cancelText={t('cancel') || 'Cancel'}
        centered
        width={520}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item
            name="name"
            label={t('agentName') || 'Agent Name'}
            rules={[{ required: true, message: t('nameRequired') || 'Name is required' }]}
          >
            <Input className="rounded-lg" />
          </Form.Item>
          <Form.Item name="type" label={t('agentType') || 'Agent Type'} rules={[{ required: true, message: t('typeRequired') || 'Type is required' }]}>
            <Select className="rounded-lg" placeholder={t('typePlaceholder') || 'Select type'}>
              <Select.Option value="orchestrator">{t('orchestrator.name')}</Select.Option>
              <Select.Option value="faq">{t('faq.name')}</Select.Option>
              <Select.Option value="after-sale">{t('aftersales.name')}</Select.Option>
              <Select.Option value="custom">{t('custom.name')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="description" label={t('agentDesc') || 'Description'}>
            <TextArea rows={3} className="rounded-lg" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
