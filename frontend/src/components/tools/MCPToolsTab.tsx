'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { useTranslations } from 'next-intl';
import { toolsApi } from '@/lib/api';
import { message } from 'antd';

interface MCPTool {
  id: string;
  name: string;
  icon: string;
  description: string;
  isEnabled: boolean;
}

interface MCPServerGroup {
  serverName: string;
  serverId: string;
  tools: MCPTool[];
}

export interface MCPToolsTabHandle {
  refresh: () => void;
}

const MCPToolsTab = forwardRef<MCPToolsTabHandle, { activeTab: string; refreshKey: number }>((props, ref) => {
  const { activeTab, refreshKey } = props;
  const t = useTranslations('Tools.mcpTools');
  const [serverGroups, setServerGroups] = useState<MCPServerGroup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (activeTab === 'mcptools') {
      fetchMcpTools();
    }
  }, [activeTab, refreshKey]);

  useImperativeHandle(ref, () => ({
    refresh: () => {
      fetchMcpTools();
    },
  }));

  const fetchMcpTools = async () => {
    try {
      setLoading(true);
      const res: any = await toolsApi.getMcpTools();
      const data = res?.data ?? res;
      const rawGroups = Array.isArray(data) ? data : [];
      const mapped = rawGroups.map((group: any) => ({
        serverId: group.server_id,
        serverName: group.server_name,
        tools: (group.tools || []).map((tool: any) => ({
          id: tool.id,
          name: tool.name,
          icon: tool.icon || 'build',
          description: tool.description || '',
          isEnabled: tool.is_enabled,
        })),
      }));
      setServerGroups(mapped);
    } catch {
      setServerGroups([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = async (toolId: string) => {
    let targetGroup: MCPServerGroup | undefined;
    let targetTool: MCPTool | undefined;

    for (const group of serverGroups) {
      const tool = group.tools.find(t => t.id === toolId);
      if (tool) {
        targetGroup = group;
        targetTool = tool;
        break;
      }
    }

    if (!targetTool || !targetGroup) return;

    const newEnabled = !targetTool.isEnabled;

    setServerGroups(prev =>
      prev.map(group =>
        group.serverId === targetGroup!.serverId
          ? {
              ...group,
              tools: group.tools.map(t =>
                t.id === toolId ? { ...t, isEnabled: newEnabled } : t
              ),
            }
          : group
      )
    );

    try {
      await toolsApi.toggleMcpTool(toolId, newEnabled);
    } catch {
      setServerGroups(prev =>
        prev.map(group =>
          group.serverId === targetGroup!.serverId
            ? {
                ...group,
                tools: group.tools.map(t =>
                  t.id === toolId ? { ...t, isEnabled: !newEnabled } : t
                ),
              }
            : group
        )
      );
      message.error(t('toggleFailed') || 'Failed to update tool status');
    }
  };

  const handleToggleAllTools = async (serverId: string) => {
    setServerGroups((prev) =>
      prev.map((group) => {
        if (group.serverId !== serverId) return group;
        const allEnabled = group.tools.every((t) => t.isEnabled);
        const newEnabled = !allEnabled;
        return {
          ...group,
          tools: group.tools.map((t) => ({ ...t, isEnabled: newEnabled })),
        };
      })
    );

    try {
      const allEnabled = serverGroups.find((g) => g.serverId === serverId)?.tools.every((t) => t.isEnabled) ?? false;
      const newEnabled = !allEnabled;
      await toolsApi.bulkToggleMcpTool(serverId, newEnabled);
    } catch {
      await fetchMcpTools();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
      </div>
    );
  }

  if (serverGroups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <span className="material-symbols-outlined text-6xl text-on-surface-variant/30 mb-4">integration_instructions</span>
        <h3 className="font-h3 text-h3 text-on-surface mb-2">{t('noTools')}</h3>
        <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md">{t('noToolsHint')}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-lg">
      {serverGroups.map((group) => {
        const enabledCount = group.tools.filter(t => t.isEnabled).length;
        return (
          <div key={group.serverId} className="bg-card-bg rounded-xl border border-outline-variant shadow-soft overflow-hidden">
            <div className="px-md py-4 border-b border-outline-variant bg-surface-bright flex justify-between items-center">
              <div>
                <h3 className="font-h3 text-h3 text-on-surface">{group.serverName}</h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{t('serverLabel')}: {group.serverName}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-body-sm text-body-sm text-on-surface-variant">{t('masterToggle')}</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" checked={group.tools.every((t) => t.isEnabled)} onChange={() => handleToggleAllTools(group.serverId)} />
                  <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-light rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
                <div className="bg-primary-light text-primary px-3 py-1 rounded-full font-label-sm text-label-sm flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-primary inline-block"></span>
                  {enabledCount} {t('enabled')}
                </div>
              </div>
            </div>
            <div className="w-full">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-outline-variant bg-surface-container-lowest">
                    <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold w-1/4">{t('toolName')}</th>
                    <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold w-2/4">{t('description')}</th>
                    <th className="px-md py-3 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold w-1/4 text-right">{t('status')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant">
                  {group.tools.map((tool) => (
                    <tr key={tool.id} className="hover:bg-surface-container transition-colors group">
                      <td className="px-md py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-on-surface-variant group-hover:bg-card-bg transition-colors border border-transparent group-hover:border-outline-variant">
                            <span className="material-symbols-outlined">{tool.icon}</span>
                          </div>
                          <span className="font-label-md text-label-md text-on-surface font-medium">{tool.name}</span>
                        </div>
                      </td>
                      <td className="px-md py-4 font-body-sm text-body-sm text-on-surface-variant">
                        {tool.description}
                      </td>
                      <td className="px-md py-4 text-right">
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input 
                            type="checkbox" 
                            className="sr-only peer" 
                            checked={tool.isEnabled}
                            onChange={() => toggleTool(tool.id)}
                          />
                          <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-light rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                        </label>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
});

export default MCPToolsTab;