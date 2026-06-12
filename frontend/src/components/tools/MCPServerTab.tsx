'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Form, Input, Button, Popconfirm, App } from 'antd';
import { useTranslations } from 'next-intl';
import { settingsApi } from '@/lib/api';

export default function MCPServerTab({ onServerChange }: { onServerChange?: () => void }) {
  const { message } = App.useApp();
  const t = useTranslations('Tools.mcp');
  const [servers, setServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingServer, setEditingServer] = useState<any>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [transportType, setTransportType] = useState<'sse' | 'stdio'>('sse');
  const [argsList, setArgsList] = useState<string[]>([]);
  const [argInput, setArgInput] = useState('');
  const [envList, setEnvList] = useState<{ key: string; value: string }[]>([]);
  const [jsonInput, setJsonInput] = useState('');
  const [jsonError, setJsonError] = useState('');

  const fetchServers = useCallback(() => {
    setLoading(true);
    settingsApi.getMCPServers()
      .then((res: any) => {
        const data = res?.data ?? res;
        setServers(Array.isArray(data) ? data : data?.items ?? []);
      })
      .catch(() => {
        setServers([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  const handleConnect = () => {
    setEditingServer(null);
    form.resetFields();
    setTransportType('sse');
    setArgsList([]);
    setArgInput('');
    setEnvList([]);
    setJsonInput('');
    setJsonError('');
    setIsModalOpen(true);
  };

  const handleEdit = (server: any) => {
    setEditingServer(server);
    const serverTransport = server.transportType || server.transport_type || 'sse';
    setTransportType(serverTransport as 'sse' | 'stdio');
    form.setFieldsValue({
      name: server.name,
      url: server.url,
      command: server.command,
    });
    setArgsList(server.args || []);
    setEnvList(
      server.env
        ? Object.entries(server.env).map(([key, value]) => ({
            key,
            value: value as string,
          }))
        : []
    );
    if (serverTransport === 'stdio') {
      const serverName = server.name || 'server-name';
      const jsonConfig: Record<string, unknown> = {
        command: server.command,
        ...(server.args && server.args.length > 0 ? { args: server.args } : {}),
        ...(server.env && Object.keys(server.env).length > 0 ? { env: server.env } : {}),
      };
      setJsonInput(JSON.stringify({ mcpServers: { [serverName]: jsonConfig } }, null, 2));
    }
    setIsModalOpen(true);
  };

  const handleAddArg = () => {
    const trimmed = argInput.trim();
    if (trimmed) {
      setArgsList([...argsList, trimmed]);
      setArgInput('');
    }
  };

  const handleRemoveArg = (index: number) => {
    setArgsList(argsList.filter((_, i) => i !== index));
  };

  const handleAddEnv = () => {
    setEnvList([...envList, { key: '', value: '' }]);
  };

  const handleRemoveEnv = (index: number) => {
    setEnvList(envList.filter((_, i) => i !== index));
  };

  const handleEnvChange = (index: number, field: 'key' | 'value', val: string) => {
    const updated = [...envList];
    updated[index][field] = val;
    setEnvList(updated);
  };

  const parseJsonConfig = (input: string): { command: string; args: string[]; env: Record<string, string> } | null => {
    try {
      const parsed = JSON.parse(input);
      const config = parsed.mcpServers
        ? Object.values(parsed.mcpServers)[0] as any
        : parsed;
      if (!config?.command) return null;
      return {
        command: config.command,
        args: config.args || [],
        env: config.env || {},
      };
    } catch {
      return null;
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      const payload: Record<string, unknown> = {
        name: values.name,
        transportType,
      };

      if (transportType === 'sse') {
        payload.url = values.url;
      } else {
        const parsed = parseJsonConfig(jsonInput);
        if (!parsed) {
          setJsonError(t('jsonParseError') || 'JSON 格式错误，请检查输入');
          setSaving(false);
          return;
        }
        setJsonError('');
        payload.command = parsed.command;
        payload.args = parsed.args;
        if (Object.keys(parsed.env).length > 0) {
          payload.env = parsed.env;
        }
      }

      if (editingServer) {
        await settingsApi.updateMCPServer(editingServer.id, payload);
        message.success(t('updateSuccess') || 'Updated');
      } else {
        await settingsApi.createMCPServer(payload);
        message.success(t('createSuccess') || 'Server connected');
      }
      setIsModalOpen(false);
      fetchServers();
    } catch {
      message.error(t('saveFailed') || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (serverId: string) => {
    try {
      await settingsApi.deleteMCPServer(serverId);
      message.success(t('deleteSuccess') || 'Server deleted');
      fetchServers();
    } catch {
      message.error(t('deleteFailed') || 'Delete failed');
    }
  };

  const handleTest = async (serverId: string) => {
    try {
      setTestingId(serverId);
      const res: any = await settingsApi.testMCPServer(serverId);
      const data = res?.data;
      if (data?.status === 'online') {
        const info = [
          t('testSuccess') || 'Connection successful',
          data.latency ? ` | ${data.latency}ms` : '',
          data.toolsCount > 0 ? ` | ${data.toolsCount} tools` : '',
        ].join('');
        message.success(info, 4);
        fetchServers();
      } else {
        const errorDetail = data?.error || '';
        const warningMsg = errorDetail
          ? `${t('testWarning') || 'Connection issue'}: ${errorDetail}`
          : (t('testWarning') || 'Connection issue detected');
        message.warning(warningMsg, 5);
        fetchServers();
      }
    } catch (err: any) {
      const detail = err?.response?.data?.message || err?.message || '';
      const errorMsg = detail
        ? `${t('testFailed') || 'Connection failed'}: ${detail}`
        : (t('testFailed') || 'Connection failed');
      message.error(errorMsg, 5);
    } finally {
      setTestingId(null);
    }
  };

  const handleToggleServer = async (serverId: string) => {
    const server = servers.find((s) => s.id === serverId);
    if (!server) return;
    const newEnabled = server.isEnabled === false ? true : false;
    setServers((prev) =>
      prev.map((s) => (s.id === serverId ? { ...s, isEnabled: newEnabled } : s))
    );
    try {
      await settingsApi.toggleMCPServer(serverId, newEnabled);
      onServerChange?.();
    } catch {
      setServers((prev) =>
        prev.map((s) => (s.id === serverId ? { ...s, isEnabled: !newEnabled } : s))
      );
      message.error(t('toggleFailed') || 'Failed to toggle status');
    }
  };

  return (
    <div className="flex flex-col gap-lg">
      <div className="flex justify-between items-end mb-sm">
        <div>
          <h2 className="font-h2 text-h2 text-on-surface">{t('connectedServers')}</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-xs max-w-2xl">
            {t('desc')}
          </p>
        </div>
        <button
          onClick={handleConnect}
          className="bg-primary text-on-primary font-label-md text-label-md rounded-lg shadow-sm hover:scale-[1.02] hover:bg-primary-container hover:text-on-primary-container transition-all px-4 py-2.5 flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          {t('connectNew')}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-md">
        {loading ? (
          <div className="col-span-full flex items-center justify-center py-20">
            <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
          </div>
        ) : servers.length === 0 ? (
          <div className="col-span-full flex flex-col items-center justify-center py-20 text-on-surface-variant">
            <span className="material-symbols-outlined text-4xl mb-2">dns</span>
            <p className="font-body-md text-body-md">{t('noServers') || 'No MCP servers connected'}</p>
          </div>
        ) : (
        servers.map((server) => (
          <div
            key={server.id}
            className="bg-card-bg rounded-xl p-md border border-outline-variant shadow-soft hover:-translate-y-[2px] hover:shadow-lg transition-all flex flex-col h-full relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary-container rounded-bl-full -mr-16 -mt-16 opacity-50 group-hover:opacity-100 transition-opacity"></div>

            <div className="flex justify-between items-start mb-md relative z-10">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-surface-container flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined">{server.icon || 'dns'}</span>
                </div>
                <div>
                  <h3 className="font-h3 text-h3 text-on-surface leading-tight">{server.name}</h3>
                  <div className="flex items-center gap-2 mt-xs">
                    <span className="font-code text-code text-on-surface-variant text-[11px] px-1.5 py-0.5 rounded bg-surface-container-low border border-outline-variant">
                      {(server.transportType || server.transport_type || 'sse').toUpperCase()}
                    </span>
                    <p className="font-code text-code text-on-surface-variant text-[11px]">{server.version || '-'}</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" checked={server.isEnabled !== false} onChange={() => handleToggleServer(server.id)}/>
                  <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-light rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
                <div className={`font-label-sm text-label-sm px-2.5 py-1 rounded-full flex items-center gap-1.5 border ${
                  server.status === 'Online' || server.status === 'online'
                    ? 'bg-surface-container-low text-success border-success/20'
                    : 'bg-error-container/30 text-error border-error/20'
                }`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${server.status === 'Online' || server.status === 'online' ? 'bg-success' : 'bg-error'}`}></span>
                  {(server.status === 'Online' || server.status === 'online') ? t('online') : t('offline')}
                </div>
              </div>
            </div>

            <div className="flex-grow flex flex-col gap-sm mb-md relative z-10">
              {(server.transportType || server.transport_type) === 'stdio' ? (
                <div className="flex items-center gap-2 font-code text-code p-2 rounded border border-outline-variant text-on-surface bg-surface-container-low">
                  <span className="material-symbols-outlined text-[16px] text-outline">terminal</span>
                  <span className="truncate">{server.command} {(server.args || []).join(' ')}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 font-code text-code p-2 rounded border border-outline-variant text-on-surface bg-surface-container-low">
                  <span className="material-symbols-outlined text-[16px] text-outline">link</span>
                  <span className="truncate">{server.url || '-'}</span>
                </div>
              )}
              <div className="flex items-center gap-2 font-body-sm text-body-sm text-on-surface-variant mt-xs">
                <span className="material-symbols-outlined text-[16px]">build</span>
                {t('toolsProvided', { count: server.tools ?? server.toolsCount ?? server.tools_count ?? 0 })}
              </div>
            </div>

            <div className="border-t border-outline-variant pt-md flex items-center justify-end relative z-10 mt-auto">
              <div className="flex gap-3">
                <button
                  onClick={() => handleEdit(server)}
                  className="text-primary hover:text-primary-container font-label-md text-label-md transition-colors"
                >{t('edit')}</button>
                <button
                  onClick={() => handleTest(server.id)}
                  disabled={testingId === server.id}
                  className="text-info hover:text-primary font-label-md text-label-md transition-colors"
                >
                  {testingId === server.id ? '...' : t('test') || 'Test'}
                </button>
                <Popconfirm
                  title={t('confirmDelete') || 'Delete this server?'}
                  onConfirm={() => handleDelete(server.id)}
                  okText={t('yes') || 'Yes'}
                  cancelText={t('no') || 'No'}
                >
                  <button className="text-error hover:text-error-container font-label-md text-label-md transition-colors">{t('delete')}</button>
                </Popconfirm>
              </div>
            </div>
          </div>
        ))
        )}
      </div>

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{editingServer ? t('editTitle') || 'Edit Server' : t('modalTitle')}</span>}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        centered
        className="custom-modal"
      >
        <Form form={form} layout="vertical" className="mt-6">
          <Form.Item
            name="name"
            label={<span className="font-label-md text-on-surface">{t('serverName')}</span>}
            rules={[{ required: true, message: t('nameRequired') || 'Name is required' }]}
          >
            <Input placeholder={t('namePlaceholder')} className="h-11 rounded-lg border-outline-variant" />
          </Form.Item>

          <div className="mb-4">
            <label className="font-label-md text-on-surface block mb-2">{t('transportType')}</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setTransportType('sse')}
                className={`flex-1 py-2.5 rounded-lg font-label-md text-label-md border transition-all ${
                  transportType === 'sse'
                    ? 'bg-primary text-on-primary border-primary'
                    : 'bg-surface-container-low text-on-surface-variant border-outline-variant hover:border-primary/50'
                }`}
              >
                {t('sse')}
              </button>
              <button
                type="button"
                onClick={() => setTransportType('stdio')}
                className={`flex-1 py-2.5 rounded-lg font-label-md text-label-md border transition-all ${
                  transportType === 'stdio'
                    ? 'bg-primary text-on-primary border-primary'
                    : 'bg-surface-container-low text-on-surface-variant border-outline-variant hover:border-primary/50'
                }`}
              >
                {t('stdio')}
              </button>
            </div>
          </div>

          {transportType === 'sse' ? (
            <Form.Item
              name="url"
              label={<span className="font-label-md text-on-surface">{t('serverUrl')}</span>}
              rules={[{ required: transportType === 'sse', message: t('urlRequired') || 'URL is required' }]}
            >
              <Input placeholder={t('urlPlaceholder')} className="h-11 rounded-lg border-outline-variant" />
            </Form.Item>
          ) : (
            <div className="mb-4">
              <label className="font-label-md text-on-surface block mb-2">
                {t('jsonConfig') || 'JSON 配置'}
              </label>
              <p className="font-body-sm text-on-surface-variant mb-2">
                {t('jsonConfigDesc') || '粘贴 MCP 服务器 JSON 配置'}
              </p>
              <Input.TextArea
                value={jsonInput}
                onChange={(e) => {
                  setJsonInput(e.target.value);
                  setJsonError('');
                }}
                placeholder={`{\n  "mcpServers": {\n    "server-name": {\n      "command": "npx",\n      "args": ["-y", "server-package@latest"]\n    }\n  }\n}`}
                rows={10}
                className="font-code rounded-lg border-outline-variant"
              />
              {jsonError && <p className="text-error text-xs mt-1">{jsonError}</p>}
            </div>
          )}

          <div className="flex gap-3 mt-8">
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
              className="h-11 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-label-md border-none"
              loading={saving}
              onClick={handleSave}
            >
              {editingServer ? t('save') || 'Save' : t('connect')}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
