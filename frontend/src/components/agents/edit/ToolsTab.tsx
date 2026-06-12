'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { toolsApi, agentsApi } from '@/lib/api';

interface Tool {
  id: string;
  name: string;
  nameEn?: string;
  desc: string;
  icon: string;
  category: string;
  isBuiltin: boolean;
  isEnabled: boolean;
  active: boolean;
  tool_type?: string;
  mcp_server_id?: string;
  mcp_server_name?: string;
}

export interface ToolsTabHandle {
  save: () => Promise<boolean>;
  isDirty: () => boolean;
  refreshData: () => void;
}

const ToolsTab = forwardRef<ToolsTabHandle, { agentId: string, agentData?: Record<string, any>, dataRefreshKey?: number, linkedMcpServerIds?: string[] | null }>(function ToolsTab({ agentId, agentData, dataRefreshKey, linkedMcpServerIds }, ref) {
  const t = useTranslations('AgentEdit.tools');
  const [tools, setTools] = useState<Tool[]>([]);
  const [mcpTools, setMcpTools] = useState<Tool[]>([]);
  const [hasLinkedMcpServers, setHasLinkedMcpServers] = useState(false);
  const [originalActiveIds, setOriginalActiveIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [orphanedMcpToolIds, setOrphanedMcpToolIds] = useState<string[]>([]);
  const originalActiveIdsRef = useRef<Set<string>>(new Set());
  const prevMcpToolIdSetRef = useRef<Set<string>>(new Set());
  const currentToolsRef = useRef<Tool[]>([]);
  const currentMcpToolsRef = useRef<Tool[]>([]);

  const fetchTools = useCallback(async () => {
      try {
        setLoading(true);
        setOrphanedMcpToolIds([]);
        const prevOriginalIds = new Set(originalActiveIdsRef.current);
        const prevMcpIds = new Set(prevMcpToolIdSetRef.current);
        const toolsRes = await toolsApi.list();
        const toolList = Array.isArray(toolsRes) ? toolsRes : ((toolsRes as unknown) as Record<string, unknown>)?.data as Tool[] || ((toolsRes as unknown) as Record<string, unknown>)?.items as Tool[] || [];

        let agentToolIds: string[] = [];
        if (agentData) {
          agentToolIds = Array.isArray(agentData?.tools)
            ? agentData.tools
                .filter((t: Tool | Record<string, unknown>) => {
                  if (typeof t === 'string') return true;
                  const obj = t as Record<string, unknown>;
                  return obj.isEnabled !== false && obj.is_enabled !== false;
                })
                .map((t: Tool | Record<string, unknown>) => typeof t === 'string' ? t : (t as Record<string, unknown>).id as string)
            : [];
        }

        const builtinToolList = (toolList as Record<string, unknown>[]).filter(
          (t) => (t.toolType as string) !== 'mcp'
        );
        const mapped = builtinToolList.map((t) => ({
          ...t,
          desc: (t.description as string) || (t.desc as string) || '',
          active: (() => {
            const existing = currentToolsRef.current.find(ct => ct.id === (t.id as string));
            if (existing) return existing.active;
            return agentToolIds.includes(t.id as string);
          })(),
        })) as Tool[];
        setTools(mapped);

        const allActiveIds = new Set(mapped.filter(t => t.active).map(t => t.id));

        const linkedServerIds = new Set<string>();
        if (linkedMcpServerIds !== null && linkedMcpServerIds !== undefined) {
          linkedMcpServerIds.forEach(id => linkedServerIds.add(id));
        } else if (agentData?.mcp_servers && Array.isArray(agentData.mcp_servers)) {
          for (const s of agentData.mcp_servers) {
            if (typeof s === 'string') {
              linkedServerIds.add(s);
            } else {
              const obj = s as Record<string, unknown>;
              const sid = (obj.id as string) || (obj.server_id as string) || '';
              if (sid) linkedServerIds.add(sid);
            }
          }
        }
        setHasLinkedMcpServers(linkedServerIds.size > 0);

        let filteredMcpTools: Tool[] = [];
        if (linkedServerIds.size > 0) {
          try {
            const mcpRes = await toolsApi.getMcpTools();
            const mcpData = Array.isArray(mcpRes) ? mcpRes : ((mcpRes as unknown) as Record<string, unknown>)?.data as Record<string, unknown>[] || [];
            for (const serverGroup of mcpData as Record<string, unknown>[]) {
              const serverId = serverGroup.server_id as string;
              if (!linkedServerIds.has(serverId)) continue;
              const serverTools = serverGroup.tools as Record<string, unknown>[];
              if (!serverTools) continue;
              for (const st of serverTools) {
                if (st.is_enabled === false) continue;
                const toolId = st.id as string;
                const mcpToolActive = (() => {
                  const existing = currentMcpToolsRef.current.find(ct => ct.id === toolId);
                  if (existing) return existing.active;
                  return agentToolIds.includes(toolId);
                })();
                filteredMcpTools.push({
                  id: toolId,
                  name: (st.name as string) || toolId,
                  desc: (st.description as string) || (st.desc as string) || '',
                  icon: (st.icon as string) || 'hub',
                  category: 'mcp',
                  isBuiltin: false,
                  isEnabled: true,
                  active: mcpToolActive,
                  tool_type: 'mcp',
                  mcp_server_id: serverId,
                  mcp_server_name: (serverGroup.server_name as string) || serverId,
                });
                if (mcpToolActive) {
                  allActiveIds.add(toolId);
                }
              }
            }
          } catch {}
        }
        setMcpTools(filteredMcpTools);

        const newOrphans: string[] = [];
        prevOriginalIds.forEach((id) => {
          if (!allActiveIds.has(id)) {
            if (prevMcpIds.has(id)) {
              newOrphans.push(id);
            } else {
              allActiveIds.add(id);
            }
          }
        });

        if (newOrphans.length > 0) {
          setOrphanedMcpToolIds(prev => {
            const existing = new Set(prev);
            newOrphans.forEach(id => existing.add(id));
            return [...existing];
          });
        }

        const currentMcpIds = new Set(filteredMcpTools.map(t => t.id));
        prevMcpToolIdSetRef.current = currentMcpIds;

        setOriginalActiveIds(allActiveIds);
      } catch {
        setTools([]);
        setMcpTools([]);
      } finally {
        setLoading(false);
      }
    }, [agentData, linkedMcpServerIds]);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  useEffect(() => {
    originalActiveIdsRef.current = originalActiveIds;
  }, [originalActiveIds]);

  useEffect(() => {
    currentToolsRef.current = tools;
  }, [tools]);

  useEffect(() => {
    currentMcpToolsRef.current = mcpTools;
  }, [mcpTools]);

  const toggleTool = (id: string) => {
    setTools(prev => prev.map(t =>
      t.id === id ? { ...t, active: !t.active } : t
    ));
  };

  const toggleMcpTool = (id: string) => {
    setMcpTools(prev => prev.map(t =>
      t.id === id ? { ...t, active: !t.active } : t
    ));
  };

  const handleSave = async (): Promise<boolean> => {
    if (!agentId) return false;
    const allTools = [...tools, ...mcpTools];
    const currentActiveIds = new Set(allTools.filter(t => t.active).map(t => t.id));
    const toActivate = [...currentActiveIds].filter(id => !originalActiveIds.has(id));
    const toDeactivate = [...originalActiveIds].filter(id => !currentActiveIds.has(id));
    const orphanedToDeactivate = orphanedMcpToolIds.filter(id => !currentActiveIds.has(id));
    const allToDeactivate = [...new Set([...toDeactivate, ...orphanedToDeactivate])];
    if (toActivate.length === 0 && allToDeactivate.length === 0) return true;
    try {
      for (const toolId of toActivate) {
        await agentsApi.toggleTool(agentId, toolId, true);
      }
      for (const toolId of allToDeactivate) {
        await agentsApi.toggleTool(agentId, toolId, false);
      }
      setOriginalActiveIds(currentActiveIds);
      setOrphanedMcpToolIds([]);
      return true;
    } catch {
      return false;
    }
  };

  useImperativeHandle(ref, () => ({
    save: handleSave,
    isDirty: () => {
      const allTools = [...tools, ...mcpTools];
      const currentActiveIds = new Set(allTools.filter(t => t.active).map(t => t.id));
      const dirty = currentActiveIds.size !== originalActiveIds.size ||
        [...currentActiveIds].some(id => !originalActiveIds.has(id));
      return dirty || orphanedMcpToolIds.length > 0;
    },
    refreshData: () => {
      fetchTools();
    },
  }));

  const activeCount = tools.filter(t => t.active).length + mcpTools.filter(t => t.active).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-lg">
      <div className="bg-card-bg rounded-xl border border-outline-variant shadow-soft overflow-hidden">
        <div className="px-md py-4 border-b border-outline-variant bg-surface-bright flex justify-between items-center">
          <div>
            <h3 className="font-h3 text-h3 text-on-surface">{t('builtinTools')}</h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{t('builtinDesc')}</p>
          </div>
          <div className="bg-primary-light text-primary px-3 py-1 rounded-full font-label-sm text-label-sm flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-primary inline-block"></span>
            {t('activeCount', { count: activeCount })}
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
              {tools.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-md py-12 text-center text-on-surface-variant font-body-sm text-body-sm">
                    {t('noTools') || 'No tools available'}
                  </td>
                </tr>
              ) : (
                tools.map((tool) => (
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
                      {tool.desc}
                    </td>
                    <td className="px-md py-4 text-right">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={tool.active}
                          onChange={() => toggleTool(tool.id)}
                        />
                        <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-light rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {hasLinkedMcpServers && (
        <div className="bg-card-bg rounded-xl border border-outline-variant shadow-soft overflow-hidden">
          <div className="px-md py-4 border-b border-outline-variant bg-surface-bright flex justify-between items-center">
            <div>
              <h3 className="font-h3 text-h3 text-on-surface">{t('mcpTools')}</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{t('mcpToolsDesc')}</p>
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
                {mcpTools.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-md py-12 text-center text-on-surface-variant font-body-sm text-body-sm">
                      <p>{t('noMcpTools')}</p>
                      <p className="mt-1 text-body-xs">{t('noMcpToolsHint')}</p>
                    </td>
                  </tr>
                ) : (
                  mcpTools.map((tool) => (
                    <tr key={tool.id} className="hover:bg-surface-container transition-colors group">
                      <td className="px-md py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-on-surface-variant group-hover:bg-card-bg transition-colors border border-transparent group-hover:border-outline-variant">
                            <span className="material-symbols-outlined">{tool.icon}</span>
                          </div>
                          <div>
                            <span className="font-label-md text-label-md text-on-surface font-medium block">{tool.name}</span>
                            {tool.mcp_server_name && (
                              <span className="font-body-xs text-body-xs text-on-surface-variant">{tool.mcp_server_name}</span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-md py-4 font-body-sm text-body-sm text-on-surface-variant">
                        {tool.desc}
                      </td>
                      <td className="px-md py-4 text-right">
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={tool.active}
                            onChange={() => toggleMcpTool(tool.id)}
                          />
                          <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-light rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                        </label>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="rounded-xl border-2 border-dashed border-outline-variant bg-surface-container-low p-xl flex flex-col items-center justify-center text-center min-h-[250px] hover:border-primary transition-colors hover:bg-surface-container">
        <div className="w-16 h-16 rounded-full bg-primary-light flex items-center justify-center text-primary mb-4 shrink-0">
          <span className="material-symbols-outlined !text-[32px]">extension</span>
        </div>
        <h3 className="font-h3 text-h3 text-on-surface mb-2">{t('customToolConfig')}</h3>
        <p className="font-body-md text-body-md text-on-surface-variant max-w-[400px] w-full mx-auto mb-6">
          {t('customToolDesc')}
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-surface-variant rounded-full text-on-surface font-label-sm text-label-sm font-medium">
          <span className="material-symbols-outlined !text-[18px]">schedule</span>
          <span>{t('comingSoon')}</span>
        </div>
      </div>
    </div>
  );
});

export default ToolsTab;
