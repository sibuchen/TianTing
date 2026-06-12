'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { useTranslations } from 'next-intl';
import { App } from 'antd';
import { settingsApi, agentsApi } from '@/lib/api';

interface MCPServer {
  id: string;
  name: string;
  version: string;
  icon: string;
  url: string;
  tools: number;
  status: string;
  color: string;
  linked: boolean;
  disabled: boolean;
}

export interface MCPConfigTabHandle {
  save: () => Promise<boolean>;
  isDirty: () => boolean;
}

const MCPConfigTab = forwardRef<MCPConfigTabHandle, { agentId: string, agentData?: Record<string, any>, onServersChange?: (linkedServerIds: string[]) => void }>(function MCPConfigTab({ agentId, agentData, onServersChange }, ref) {
  const { message } = App.useApp();
  const t = useTranslations('AgentEdit.mcp');
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [originalLinkedIds, setOriginalLinkedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [newServer, setNewServer] = useState({ name: '', url: '', icon: 'cloud' });

  useEffect(() => {
    const fetchServers = async () => {
      try {
        setLoading(true);
        const serversRes = await settingsApi.getMCPServers();
        const serverList = Array.isArray(serversRes) ? serversRes : ((serversRes as unknown) as Record<string, unknown>)?.data as MCPServer[] || ((serversRes as unknown) as Record<string, unknown>)?.items as MCPServer[] || [];
        
        let linkedServerIds: string[] = [];
        if (agentData) {
          linkedServerIds = Array.isArray(agentData?.mcp_servers)
            ? (agentData.mcp_servers as Array<Record<string, unknown>>).map((s: Record<string, unknown>) => (s.id || s.mcp_server_id) as string)
            : [];
        }
        
        const enriched = (serverList as Record<string, unknown>[]).map((s) => ({
          ...s,
          status: s.status === 'online' ? 'Online' : s.status === 'offline' ? 'Offline' : s.status,
          tools: (s.toolsCount as number) ?? (s.tools_count as number) ?? (s.tools as number) ?? 0,
          linked: linkedServerIds.includes(s.id as string),
        })) as MCPServer[];
        setServers(enriched);
        setOriginalLinkedIds(new Set(linkedServerIds));
      } catch {
        setServers([]);
      } finally {
        setLoading(false);
      }
    };

    fetchServers();
  }, [agentData]);

  const refreshServers = async () => {
    try {
      const res = await settingsApi.getMCPServers();
      setServers(Array.isArray(res) ? res : ((res as unknown) as Record<string, unknown>)?.data as MCPServer[] || ((res as unknown) as Record<string, unknown>)?.items as MCPServer[] || []);
    } catch {
      // keep current state
    }
  };

  const handleToggleLink = (serverId: string, currentLinked: boolean, disabled: boolean) => {
    if (disabled) return;
    setServers(prev => {
      const updated = prev.map(s =>
        s.id === serverId ? { ...s, linked: !currentLinked } : s
      );
      const linkedIds = updated.filter(s => s.linked).map(s => s.id);
      onServersChange?.(linkedIds);
      return updated;
    });
  };

  const handleCreateServer = async () => {
    if (!newServer.name || !newServer.url) return;
    try {
      await settingsApi.createMCPServer({
        name: newServer.name,
        url: newServer.url,
        icon: newServer.icon,
        agentId,
      });
      setShowConnectDialog(false);
      setNewServer({ name: '', url: '', icon: 'cloud' });
      refreshServers();
    } catch {
      // handle error silently
    }
  };

  const handleSave = async (): Promise<boolean> => {
    if (!agentId) return false;
    const currentLinkedIds = new Set(servers.filter(s => s.linked).map(s => s.id));
    const toLink = [...currentLinkedIds].filter(id => !originalLinkedIds.has(id));
    const toUnlink = [...originalLinkedIds].filter(id => !currentLinkedIds.has(id));
    if (toLink.length === 0 && toUnlink.length === 0) return true;
    try {
      for (const serverId of toLink) {
        await agentsApi.linkMCPServer(agentId, serverId, true);
      }
      for (const serverId of toUnlink) {
        await agentsApi.unlinkMCPServer(agentId, serverId);
      }
      setOriginalLinkedIds(currentLinkedIds);
      return true;
    } catch {
      message.error(t('linkFailed') || 'MCP 服务器保存失败');
      return false;
    }
  };

  useImperativeHandle(ref, () => ({
    save: handleSave,
    isDirty: () => {
      const currentLinkedIds = new Set(servers.filter(s => s.linked).map(s => s.id));
      return currentLinkedIds.size !== originalLinkedIds.size || [...currentLinkedIds].some(id => !originalLinkedIds.has(id));
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
      <div className="flex justify-between items-end mb-sm">
        <div>
          <h2 className="font-h2 text-h2 text-on-surface">{t('connectedServers')}</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-xs max-w-2xl">
            {t('mcpDesc')}
          </p>
        </div>
        <button
          onClick={() => setShowConnectDialog(true)}
          className="bg-primary text-on-primary font-label-md text-label-md rounded-lg shadow-sm hover:scale-[1.02] hover:bg-primary-container hover:text-on-primary-container transition-all px-4 py-2.5 flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          {t('connectNew')}
        </button>
      </div>

      {servers.length === 0 ? (
        <div className="flex items-center justify-center py-16 text-on-surface-variant font-body-sm text-body-sm">
          {t('noServers') || 'No MCP servers configured'}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-md">
          {servers.map((server) => (
            <div
              key={server.id}
              className={`bg-card-bg rounded-xl p-md border border-outline-variant shadow-soft hover:-translate-y-[2px] hover:shadow-lg transition-all flex flex-col h-full relative overflow-hidden group ${server.disabled ? 'opacity-80' : ''}`}
            >
              {!server.disabled && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary-light rounded-bl-full -mr-16 -mt-16 opacity-50 group-hover:opacity-100 transition-opacity"></div>
              )}

              <div className="flex justify-between items-start mb-md relative z-10">
                <div className="flex items-center gap-3">
                  <div className={`h-10 w-10 rounded-lg bg-surface-container flex items-center justify-center ${server.disabled ? 'text-outline' : 'text-primary'}`}>
                    <span className="material-symbols-outlined">{server.icon}</span>
                  </div>
                  <div>
                    <h3 className="font-h3 text-h3 text-on-surface leading-tight">{server.name}</h3>
                    <p className="font-code text-code text-on-surface-variant text-[11px] mt-xs">{server.version}</p>
                  </div>
                </div>
                <div className={`font-label-sm text-label-sm px-2.5 py-1 rounded-full flex items-center gap-1.5 border ${
                  server.status === 'Online'
                    ? 'bg-surface-container-low text-success border-success/20'
                    : 'bg-error-container/30 text-error border-error/20'
                }`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${server.status === 'Online' ? 'bg-success' : 'bg-error'}`}></span>
                  {server.status}
                </div>
              </div>

              <div className="flex-grow flex flex-col gap-sm mb-md relative z-10">
                <div className={`flex items-center gap-2 font-code text-code p-2 rounded border border-outline-variant ${
                  server.disabled ? 'text-on-surface-variant bg-surface opacity-70' : 'text-on-surface bg-surface'
                }`}>
                  <span className="material-symbols-outlined text-[16px] text-outline">
                    {server.disabled ? 'link_off' : 'link'}
                  </span>
                  <span className={`truncate ${server.disabled ? 'line-through' : ''}`}>{server.url}</span>
                </div>
                <div className="flex items-center gap-2 font-body-sm text-body-sm text-on-surface-variant mt-xs">
                  <span className="material-symbols-outlined text-[16px]">build</span>
                  {t('providesTools', { count: server.tools })}
                </div>
              </div>

              <div className="border-t border-outline-variant pt-md flex items-center justify-between relative z-10 mt-auto">
                <span className={`font-label-md text-label-md ${server.disabled ? 'text-on-surface-variant' : 'text-on-surface'}`}>
                  {t('agentStatus')}
                </span>
                <label className={`flex items-center relative ${server.disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={server.linked}
                    disabled={server.disabled}
                    onChange={() => handleToggleLink(server.id, server.linked, server.disabled)}
                  />
                  <div className="w-10 h-5 bg-surface-container-high peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                  <span className={`ml-2 font-label-sm text-label-sm ${
                    server.disabled ? 'text-on-surface-variant' : server.linked ? 'text-primary' : 'text-on-surface-variant'
                  }`}>
                    {server.linked ? t('linked') : t('unlinked')}
                  </span>
                </label>
              </div>
            </div>
          ))}
        </div>
      )}

      {showConnectDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowConnectDialog(false)}>
          <div className="bg-surface-container-lowest rounded-xl shadow-lg border border-outline-variant p-lg w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-md">
              <h3 className="font-h3 text-h3 text-on-surface">{t('connectNew')}</h3>
              <button onClick={() => setShowConnectDialog(false)} className="text-on-surface-variant hover:text-on-surface transition-colors">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="flex flex-col gap-md">
              <div className="flex flex-col gap-2">
                <label className="font-label-sm text-label-sm text-on-surface-variant">{t('serverName') || 'Server Name'}</label>
                <input
                  className="w-full px-3 py-2 bg-background border border-outline-variant rounded-lg font-body-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="My MCP Server"
                  value={newServer.name}
                  onChange={(e) => setNewServer(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="font-label-sm text-label-sm text-on-surface-variant">{t('serverUrl') || 'Server URL'}</label>
                <input
                  className="w-full px-3 py-2 bg-background border border-outline-variant rounded-lg font-body-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="http://localhost:8080/mcp"
                  value={newServer.url}
                  onChange={(e) => setNewServer(prev => ({ ...prev, url: e.target.value }))}
                />
              </div>
              <div className="flex justify-end gap-sm mt-md">
                <button
                  onClick={() => setShowConnectDialog(false)}
                  className="px-4 py-2 rounded-lg border border-outline-variant text-on-surface hover:bg-surface-container-low transition-colors text-sm font-medium"
                >
                  {t('cancel') || 'Cancel'}
                </button>
                <button
                  onClick={handleCreateServer}
                  disabled={!newServer.name || !newServer.url}
                  className="px-4 py-2 rounded-lg bg-primary text-on-primary hover:bg-primary-container transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {t('connect') || 'Connect'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

export default MCPConfigTab;
