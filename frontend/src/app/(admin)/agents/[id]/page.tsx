'use client';

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { message } from 'antd';
import GeneralInfoTab, { GeneralInfoTabHandle } from '@/components/agents/edit/GeneralInfoTab';
import ModelBindingTab, { ModelBindingTabHandle } from '@/components/agents/edit/ModelBindingTab';
import SkillsTab, { SkillsTabHandle } from '@/components/agents/edit/SkillsTab';
import MCPConfigTab, { MCPConfigTabHandle } from '@/components/agents/edit/MCPConfigTab';
import ToolsTab, { ToolsTabHandle } from '@/components/agents/edit/ToolsTab';
import KnowledgeTab, { KnowledgeTabHandle } from '@/components/agents/edit/KnowledgeTab';
import QATab, { QATabHandle } from '@/components/agents/edit/QATab';
import { SlidingSwitch } from '@/components/ui/SlidingSwitch';
import { agentsApi } from '@/lib/api';

type TabId = 'general' | 'model' | 'skills' | 'mcp' | 'tools' | 'knowledge' | 'qa';

export default function AgentEditPage() {
  const t = useTranslations('AgentEdit');
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  const [activeTab, setActiveTab] = useState<TabId>('general');
  const [agentData, setAgentData] = useState<Record<string, unknown> | null>(null);
  const [saving, setSaving] = useState(false);
  const [linkedMcpServerIds, setLinkedMcpServerIds] = useState<string[] | null>(null);
  const generalInfoRef = useRef<GeneralInfoTabHandle>(null);
  const modelBindingRef = useRef<ModelBindingTabHandle>(null);
  const skillsRef = useRef<SkillsTabHandle>(null);
  const mcpConfigRef = useRef<MCPConfigTabHandle>(null);
  const toolsRef = useRef<ToolsTabHandle>(null);
  const knowledgeRef = useRef<KnowledgeTabHandle>(null);
  const qaRef = useRef<QATabHandle>(null);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    agentsApi.get(agentId).then((res: unknown) => {
      const data = (res as Record<string, unknown>)?.data
        ? (res as Record<string, unknown>).data as Record<string, unknown>
        : (res as Record<string, unknown>);
      setAgentData(data);
    }).catch(() => {
      message.error(t('general.loadFailed') || 'Failed to load agent data');
    }).finally(() => {
      setLoading(false);
    });
  }, [agentId, t]);

  const agentType = (agentData?.type ?? agentData?.agent_type ?? 'orchestrator') as string;
  const isOrchestrator = agentType === 'orchestrator';

  const tabs = useMemo(() => {
    const baseTabs = [
      { id: 'general' as TabId, label: t('tabs.general') },
      { id: 'model' as TabId, label: t('tabs.model') },
      { id: 'skills' as TabId, label: t('tabs.skills') },
      { id: 'mcp' as TabId, label: t('tabs.mcp') },
      { id: 'tools' as TabId, label: t('tabs.tools') },
    ];
    if (!isOrchestrator) {
      baseTabs.push(
        { id: 'knowledge' as TabId, label: t('tabs.knowledge') },
        { id: 'qa' as TabId, label: t('tabs.qa') },
      );
    }
    return baseTabs;
  }, [isOrchestrator, t]);

  const agentDisplayName = agentData?.name
    ? String(agentData.name)
    : agentData?.type
      ? t(`types.${agentData.type}`, { defaultValue: String(agentData.type) })
      : '...';

  const checkUnsavedChanges = useCallback(() => {
    return !!(
      generalInfoRef.current?.isDirty() ||
      modelBindingRef.current?.isDirty() ||
      skillsRef.current?.isDirty() ||
      mcpConfigRef.current?.isDirty() ||
      toolsRef.current?.isDirty() ||
      (!isOrchestrator && knowledgeRef.current?.isDirty()) ||
      (!isOrchestrator && qaRef.current?.isDirty())
    );
  }, [isOrchestrator]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (checkUnsavedChanges()) {
        e.preventDefault();
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [checkUnsavedChanges]);

  const handleGoBack = useCallback(() => {
    if (checkUnsavedChanges()) {
      const confirmed = window.confirm(t('unsavedChanges') || 'You have unsaved changes. Are you sure you want to leave?');
      if (!confirmed) return;
    }
    router.back();
  }, [checkUnsavedChanges, router, t]);

  const handleTabChange = (newTab: string) => {
    setActiveTab(newTab as TabId);
  };

  const handleMcpServersChange = useCallback((linkedIds: string[]) => {
    setLinkedMcpServerIds(linkedIds);
  }, []);

  useEffect(() => {
    if (linkedMcpServerIds !== null) {
      toolsRef.current?.refreshData();
    }
  }, [linkedMcpServerIds]);

  const handleSaveAll = async () => {
    setSaving(true);
    try {
      const savePromises = [
        generalInfoRef.current?.save(),
        modelBindingRef.current?.save(),
        skillsRef.current?.save(),
        mcpConfigRef.current?.save(),
        toolsRef.current?.save(),
        ...(!isOrchestrator ? [knowledgeRef.current?.save(), qaRef.current?.save()] : []),
      ].filter((p): p is Promise<boolean> => p !== undefined);
      const results = await Promise.allSettled(savePromises);
      const failed = results.filter(r => r.status === 'rejected' || (r.status === 'fulfilled' && r.value === false));
      if (failed.length > 0) {
        message.error(t('saveFailed') || 'Save failed');
      } else {
        message.success(t('saveSuccess') || 'Saved');
      }
    } catch {
      message.error(t('saveFailed') || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <span className="material-symbols-outlined animate-spin text-primary text-4xl">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleGoBack}
              className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-surface-variant transition-colors"
            >
              <span className="material-symbols-outlined text-[24px]">arrow_back</span>
            </button>
            <div>
              <h2 className="text-2xl font-semibold text-on-surface">{t('editAgent')}</h2>
              <p className="text-sm text-on-surface-variant mt-1 flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-primary">robot_2</span>
                {t('configuring')}: <span className="font-medium text-on-surface">{agentDisplayName}</span>
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleGoBack}
              className="px-4 py-2 rounded-lg border border-outline-variant text-on-surface hover:bg-surface-container-low hover:scale-[1.02] transition-all text-sm font-medium"
            >
              {t('cancel')}
            </button>
            <button
              onClick={handleSaveAll}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-primary text-on-primary hover:bg-primary-container hover:scale-[1.02] transition-all shadow-sm text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[20px]">save</span>
              {saving ? (t('saving') || 'Saving...') : t('saveChanges')}
            </button>
          </div>
        </div>

      <SlidingSwitch
        value={activeTab}
        onChange={handleTabChange}
        className="w-full"
        options={tabs.map(tab => ({ label: tab.label, value: tab.id }))}
      />

      <div style={{ display: activeTab === 'general' ? 'block' : 'none' }}>
        <GeneralInfoTab ref={generalInfoRef} agentId={agentId} agentData={agentData!} />
      </div>
      <div style={{ display: activeTab === 'model' ? 'block' : 'none' }}>
        <ModelBindingTab ref={modelBindingRef} agentId={agentId} agentData={agentData!} />
      </div>
      <div style={{ display: activeTab === 'skills' ? 'block' : 'none' }}>
        <SkillsTab ref={skillsRef} agentId={agentId} agentData={agentData!} />
      </div>
      <div style={{ display: activeTab === 'mcp' ? 'block' : 'none' }}>
        <MCPConfigTab ref={mcpConfigRef} agentId={agentId} agentData={agentData!} onServersChange={handleMcpServersChange} />
      </div>
      <div style={{ display: activeTab === 'tools' ? 'block' : 'none' }}>
        <ToolsTab ref={toolsRef} agentId={agentId} agentData={agentData!} linkedMcpServerIds={linkedMcpServerIds} />
      </div>
      {!isOrchestrator && (
        <>
          <div style={{ display: activeTab === 'knowledge' ? 'block' : 'none' }}>
            <KnowledgeTab ref={knowledgeRef} agentId={agentId} agentData={agentData!} />
          </div>
          <div style={{ display: activeTab === 'qa' ? 'block' : 'none' }}>
            <QATab ref={qaRef} agentId={agentId} agentData={agentData!} />
          </div>
        </>
      )}
      </div>
    </div>
  );
}
