'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle, KeyboardEvent } from 'react';
import { useTranslations } from 'next-intl';
import { App } from 'antd';
import { FluidDropdown } from '@/components/ui/fluid-dropdown';
import { Route, Zap, Headset, Settings } from 'lucide-react';
import { agentsApi, usersApi } from '@/lib/api';

interface SubAgent {
  id: string;
  name: string;
  type: string;
}

interface HumanAgent {
  id: string;
  username: string;
  email?: string;
  role?: string;
}

interface GeneralInfoTabProps {
  agentId?: string;
  agentData?: Record<string, any>;
}

export interface GeneralInfoTabHandle {
  save: () => Promise<boolean>;
  isDirty: () => boolean;
}

const GeneralInfoTab = forwardRef<GeneralInfoTabHandle, GeneralInfoTabProps>(function GeneralInfoTab({ agentId, agentData }, ref) {
  const { message } = App.useApp();
  const t = useTranslations('AgentEdit.general');
  const [isEnabled, setIsEnabled] = useState(true);
  const [agentType, setAgentType] = useState('orchestrator');
  const [agentName, setAgentName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');
  const [loading, setLoading] = useState(!!agentId);
  const [saving, setSaving] = useState(false);
  const [originalName, setOriginalName] = useState('');
  const [originalDescription, setOriginalDescription] = useState('');
  const [originalSystemPrompt, setOriginalSystemPrompt] = useState('');
  const [originalType, setOriginalType] = useState('orchestrator');

  const [subAgents, setSubAgents] = useState<SubAgent[]>([]);
  const [selectedSubAgentIds, setSelectedSubAgentIds] = useState<Set<string>>(new Set());
  const [originalSubAgentIds, setOriginalSubAgentIds] = useState<Set<string>>(new Set());

  const [supportedChannels, setSupportedChannels] = useState<string[]>([]);
  const [originalChannels, setOriginalChannels] = useState<string[]>([]);

  const [transferKeywords, setTransferKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [originalKeywords, setOriginalKeywords] = useState<string[]>([]);

  const [humanAgents, setHumanAgents] = useState<HumanAgent[]>([]);
  const [humanAgentId, setHumanAgentId] = useState('');
  const [originalHumanAgentId, setOriginalHumanAgentId] = useState('');
  const [humanAgentDropdownOpen, setHumanAgentDropdownOpen] = useState(false);

  useEffect(() => {
    if (!agentData) {
      setLoading(false);
      return;
    }
    const data = agentData;
    setAgentName(data.name ?? '');
    setOriginalName(data.name ?? '');
    setAgentType(data.type ?? data.agent_type ?? 'orchestrator');
    setOriginalType(data.type ?? data.agent_type ?? 'orchestrator');
    setDescription(data.description ?? '');
    setOriginalDescription(data.description ?? '');
    setSystemPrompt(data.system_prompt ?? data.systemPrompt ?? '');
    setOriginalSystemPrompt(data.system_prompt ?? data.systemPrompt ?? '');
    setIsEnabled(data.is_enabled ?? data.isEnabled ?? true);
    setLastUpdated(data.updated_at ?? data.updatedAt ?? '');

    const subAgentList: SubAgent[] = Array.isArray(data.subAgents)
      ? data.subAgents
      : Array.isArray(data.sub_agents)
      ? data.sub_agents
      : [];
    const subIds = new Set(subAgentList.map((s: SubAgent | Record<string, unknown>) =>
      typeof s === 'string' ? s : (s as Record<string, unknown>).id as string
    ));
    setSelectedSubAgentIds(subIds);
    setOriginalSubAgentIds(new Set(subIds));

    const channels: string[] = Array.isArray(data.supportedChannels)
      ? data.supportedChannels
      : Array.isArray(data.supported_channels)
      ? data.supported_channels
      : [];
    setSupportedChannels(channels);
    setOriginalChannels([...channels]);

    const keywords: string[] = Array.isArray(data.transferKeywords)
      ? data.transferKeywords
      : Array.isArray(data.transfer_keywords)
      ? data.transfer_keywords
      : [];
    setTransferKeywords(keywords);
    setOriginalKeywords([...keywords]);

    const hId = data.humanAgentId ?? data.human_agent_id ?? '';
    setHumanAgentId(hId);
    setOriginalHumanAgentId(hId);
    
    setLoading(false);
  }, [agentData]);

  useEffect(() => {
    if (agentType !== 'orchestrator') return;
    agentsApi.list()
      .then((res: any) => {
        const list = Array.isArray(res) ? res : res?.data?.items ?? res?.data ?? res?.items ?? [];
        const nonOrchestrator = list
          .filter((a: Record<string, unknown>) => a.type !== 'orchestrator' && a.id !== agentId)
          .map((a: Record<string, unknown>) => ({ id: a.id as string, name: (a.name as string) || '', type: (a.type as string) || '' }));
        setSubAgents(nonOrchestrator);
      })
      .catch(() => {});

    usersApi.list({ role: 'operator' })
      .then((res: any) => {
        const list = Array.isArray(res) ? res : res?.data?.items ?? res?.data ?? res?.items ?? [];
        const operators = list.map((u: Record<string, unknown>) => ({
          id: u.id as string,
          username: (u.username as string) || '',
          email: (u.email as string) || '',
          role: (u.role as string) || '',
        }));
        setHumanAgents(operators);
      })
      .catch(() => {});
  }, [agentType, agentId]);

  const handleToggle = async () => {
    const newValue = !isEnabled;
    if (!agentId) {
      setIsEnabled(newValue);
      return;
    }
    try {
      await agentsApi.toggle(agentId, newValue);
      setIsEnabled(newValue);
      message.success(t('toggleSuccess') || 'Status updated');
    } catch {
      message.error(t('toggleFailed') || 'Failed to toggle');
    }
  };

  const toggleSubAgent = (id: string) => {
    setSelectedSubAgentIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleChannel = (channel: string) => {
    setSupportedChannels(prev =>
      prev.includes(channel) ? prev.filter(c => c !== channel) : [...prev, channel]
    );
  };

  const addKeyword = () => {
    const trimmed = keywordInput.trim();
    if (trimmed && !transferKeywords.includes(trimmed)) {
      setTransferKeywords(prev => [...prev, trimmed]);
    }
    setKeywordInput('');
  };

  const removeKeyword = (kw: string) => {
    setTransferKeywords(prev => prev.filter(k => k !== kw));
  };

  const handleKeywordKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addKeyword();
    }
  };

  const handleSave = async (): Promise<boolean> => {
    if (!agentId) return true;
    const nameChanged = agentName !== originalName;
    const typeChanged = agentType !== originalType;
    const descChanged = description !== originalDescription;
    const promptChanged = systemPrompt !== originalSystemPrompt;
    const subAgentsChanged = selectedSubAgentIds.size !== originalSubAgentIds.size || [...selectedSubAgentIds].some(id => !originalSubAgentIds.has(id));
    const channelsChanged = JSON.stringify(supportedChannels) !== JSON.stringify(originalChannels);
    const keywordsChanged = JSON.stringify(transferKeywords) !== JSON.stringify(originalKeywords);
    const humanAgentChanged = humanAgentId !== originalHumanAgentId;
    if (!nameChanged && !typeChanged && !descChanged && !promptChanged && !subAgentsChanged && !channelsChanged && !keywordsChanged && !humanAgentChanged) return true;
    try {
      setSaving(true);
      await agentsApi.update(agentId, {
        name: agentName,
        type: agentType,
        description,
        systemPrompt: systemPrompt,
        supportedChannels: supportedChannels,
        transferKeywords: transferKeywords,
        humanAgentId: humanAgentId || null,
      });

      if (agentType === 'orchestrator') {
        const toAdd = [...selectedSubAgentIds].filter(id => !originalSubAgentIds.has(id));
        const toRemove = [...originalSubAgentIds].filter(id => !selectedSubAgentIds.has(id));
        for (const subId of toAdd) {
          await agentsApi.addSubAgent(agentId, subId);
        }
        for (const subId of toRemove) {
          await agentsApi.removeSubAgent(agentId, subId);
        }
        setOriginalSubAgentIds(new Set(selectedSubAgentIds));
      }

      setOriginalChannels([...supportedChannels]);
      setOriginalKeywords([...transferKeywords]);
      setOriginalHumanAgentId(humanAgentId);
      setOriginalName(agentName);
      setOriginalType(agentType);
      setOriginalDescription(description);
      setOriginalSystemPrompt(systemPrompt);

      message.success(t('saveSuccess') || 'Saved');
      return true;
    } catch {
      message.error(t('saveFailed') || 'Save failed');
      return false;
    } finally {
      setSaving(false);
    }
  };

  useImperativeHandle(ref, () => ({
    save: handleSave,
    isDirty: () => {
      const nameChanged = agentName !== originalName;
      const typeChanged = agentType !== originalType;
      const descChanged = description !== originalDescription;
      const promptChanged = systemPrompt !== originalSystemPrompt;
      const subAgentsChanged = selectedSubAgentIds.size !== originalSubAgentIds.size || [...selectedSubAgentIds].some(id => !originalSubAgentIds.has(id));
      const channelsChanged = JSON.stringify(supportedChannels) !== JSON.stringify(originalChannels);
      const keywordsChanged = JSON.stringify(transferKeywords) !== JSON.stringify(originalKeywords);
      const humanAgentChanged = humanAgentId !== originalHumanAgentId;
      return nameChanged || typeChanged || descChanged || promptChanged || subAgentsChanged || channelsChanged || keywordsChanged || humanAgentChanged;
    },
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
      </div>
    );
  }

  const selectedHumanAgent = humanAgents.find(h => h.id === humanAgentId);

  return (
    <div className="grid grid-cols-12 gap-lg">
      <div className="col-span-8 flex flex-col gap-lg">
        <div className="bg-card-bg rounded-xl p-lg shadow-soft flex flex-col gap-lg border border-outline-variant hover:-translate-y-[2px] transition-transform duration-300">
          <div className="grid grid-cols-2 gap-lg">
            <div className="flex flex-col gap-sm">
              <label className="font-label-md text-label-md text-on-surface">{t('agentName')}</label>
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-md py-sm font-body-md text-body-md text-on-surface focus:border-primary focus:ring-2 focus:ring-primary-light transition-all outline-none"
                type="text"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-sm relative">
              <label className="font-label-md text-label-md text-on-surface">{t('agentType')}</label>
              <FluidDropdown
                value={agentType}
                onChange={setAgentType}
                className="w-full"
                options={[
                  { id: 'orchestrator', label: t('orchestratorAgent'), icon: Route, color: '#3b82f6' },
                  { id: 'faq', label: t('faqAgent'), icon: Zap, color: '#f59e0b' },
                  { id: 'after-sale', label: t('afterSaleAgent'), icon: Headset, color: '#10b981' },
                  { id: 'custom', label: t('customAgent'), icon: Settings, color: '#8b5cf6' },
                ]}
              />
            </div>
          </div>
          <div className="flex flex-col gap-sm">
            <label className="font-label-md text-label-md text-on-surface">{t('description')}</label>
            <textarea
              className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-md py-sm font-body-md text-body-md text-on-surface focus:border-primary focus:ring-2 focus:ring-primary-light transition-all outline-none resize-none"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            ></textarea>
          </div>
        </div>

        <div className="bg-card-bg rounded-xl p-lg shadow-soft flex flex-col gap-md border border-outline-variant hover:-translate-y-[2px] transition-transform duration-300">
          <div className="flex justify-between items-center">
            <label className="font-label-md text-label-md text-on-surface flex items-center gap-xs">
              <span className="material-symbols-outlined text-[18px] text-primary">terminal</span>
              {t('systemPrompt')}
            </label>
            <button className="text-primary hover:text-primary-container font-label-sm text-label-sm flex items-center gap-xs transition-colors">
              <span className="material-symbols-outlined text-[16px]">magic_button</span>
              {t('optimizePrompt')}
            </button>
          </div>
          <div className="relative rounded-lg bg-surface-container-highest border border-outline-variant overflow-hidden group">
            <div className="absolute top-0 left-0 w-8 h-full bg-surface-container-low border-r border-outline-variant flex flex-col items-center py-sm text-on-surface-variant font-code text-[11px] leading-[20px] select-none pointer-events-none">
              <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span><span>7</span><span>8</span>
            </div>
            <textarea
              className="w-full bg-transparent text-on-surface font-code text-code pl-10 pr-md py-sm border-none focus:ring-0 resize-y outline-none leading-[20px] scrollbar-thin"
              rows={8}
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
            ></textarea>
          </div>

        </div>

        {agentType === 'orchestrator' && (
          <div className="grid grid-cols-2 gap-md">
            <div className="bg-card-bg rounded-xl p-lg shadow-soft flex flex-col gap-md border border-outline-variant border-l-2 border-l-primary">
              <h3 className="font-h3 text-h3 text-on-surface border-b border-outline-variant pb-sm mb-sm flex items-center gap-xs">
                <span className="material-symbols-outlined text-[18px] text-primary">account_tree</span>
                {t('subAgents')}
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">{t('subAgentsDesc')}</p>
              {subAgents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-md text-on-surface-variant">
                  <span className="material-symbols-outlined text-[32px] mb-xs opacity-40">group_off</span>
                  <span className="font-body-sm text-body-sm italic">{t('noSubAgents')}</span>
                </div>
              ) : (
                <div className="flex flex-col gap-sm max-h-48 overflow-y-auto">
                  {subAgents.map((sa) => (
                    <div
                      key={sa.id}
                      onClick={() => toggleSubAgent(sa.id)}
                      className={selectedSubAgentIds.has(sa.id)
                        ? "flex items-center gap-sm cursor-pointer rounded-lg px-sm py-sm border border-primary/40 bg-primary/5 hover:bg-primary/10 transition-colors"
                        : "flex items-center gap-sm cursor-pointer rounded-lg px-sm py-sm border border-outline-variant hover:border-primary/30 hover:bg-surface-container-low transition-colors"
                      }
                    >
                      {selectedSubAgentIds.has(sa.id) ? (
                        <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                          <span className="material-symbols-outlined text-[12px] text-on-primary">check</span>
                        </div>
                      ) : (
                        <div className="w-5 h-5 rounded-full border-2 border-outline-variant flex-shrink-0"></div>
                      )}
                      <span className="font-body-sm text-body-sm text-on-surface">{sa.name}</span>
                      <span className="ml-auto px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm border border-outline-variant/50">{sa.type}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-card-bg rounded-xl p-lg shadow-soft flex flex-col gap-md border border-outline-variant border-l-2 border-l-info">
              <h3 className="font-h3 text-h3 text-on-surface border-b border-outline-variant pb-sm mb-sm flex items-center gap-xs">
                <span className="material-symbols-outlined text-[18px] text-info">chat</span>
                {t('channels')}
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">{t('channelsDesc')}</p>
              <div className="flex flex-col gap-sm">
                <div
                  onClick={() => toggleChannel('web')}
                  className={`flex items-center gap-sm cursor-pointer rounded-lg px-sm py-sm border transition-colors ${
                    supportedChannels.includes('web')
                      ? 'border-slate-400/50 bg-slate-50/50'
                      : 'border-outline-variant hover:border-slate-300/50'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    supportedChannels.includes('web') ? 'bg-slate-100 text-slate-600' : 'bg-surface-container text-on-surface-variant'
                  }`}>
                    <span className="material-symbols-outlined text-[18px]">language</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="font-label-md text-label-md text-on-surface">{t('channelWeb')}</span>
                  </div>
                  {supportedChannels.includes('web') && (
                    <div className="ml-auto w-5 h-5 rounded-full bg-slate-500 flex items-center justify-center">
                      <span className="material-symbols-outlined text-[12px] text-white">check</span>
                    </div>
                  )}
                </div>
                <div
                  onClick={() => toggleChannel('feishu')}
                  className={`flex items-center gap-sm cursor-pointer rounded-lg px-sm py-sm border transition-colors ${
                    supportedChannels.includes('feishu')
                      ? 'border-blue-400/50 bg-blue-50/50'
                      : 'border-outline-variant hover:border-blue-300/50'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    supportedChannels.includes('feishu') ? 'bg-blue-100 text-blue-600' : 'bg-surface-container text-on-surface-variant'
                  }`}>
                    <span className="material-symbols-outlined text-[18px]">flutter_dash</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="font-label-md text-label-md text-on-surface">{t('channelFeishu')}</span>
                  </div>
                  {supportedChannels.includes('feishu') && (
                    <div className="ml-auto w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                      <span className="material-symbols-outlined text-[12px] text-white">check</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-card-bg rounded-xl p-lg shadow-soft flex flex-col gap-md border border-outline-variant border-l-2 border-l-warning">
              <h3 className="font-h3 text-h3 text-on-surface border-b border-outline-variant pb-sm mb-sm flex items-center gap-xs">
                <span className="material-symbols-outlined text-[18px] text-warning">swap_horiz</span>
                {t('transferKeywords')}
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">{t('transferKeywordsDesc')}</p>
              <div className="flex flex-wrap gap-sm">
                {transferKeywords.map((kw) => (
                  <span key={kw} className="inline-flex items-center gap-xs bg-warning/10 text-warning px-sm py-xs rounded-full border border-warning/20">
                    <span className="font-label-sm text-label-sm">{kw}</span>
                    <button
                      onClick={() => removeKeyword(kw)}
                      className="text-warning/60 hover:text-error transition-colors flex items-center justify-center rounded-full hover:bg-error/10 p-0.5"
                    >
                      <span className="material-symbols-outlined text-[14px]">close</span>
                    </button>
                  </span>
                ))}
              </div>
              <input
                className="w-full bg-surface-container-lowest border border-dashed border-outline-variant rounded-lg px-md py-sm font-body-sm text-body-sm text-on-surface focus:border-warning focus:ring-2 focus:ring-warning/20 transition-all outline-none"
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={handleKeywordKeyDown}
                placeholder={t('transferKeywordsPlaceholder')}
              />
            </div>

            <div className="bg-card-bg rounded-xl p-lg shadow-soft flex flex-col gap-md border border-outline-variant border-l-2 border-l-secondary">
              <h3 className="font-h3 text-h3 text-on-surface border-b border-outline-variant pb-sm mb-sm flex items-center gap-xs">
                <span className="material-symbols-outlined text-[18px] text-secondary">support_agent</span>
                {t('humanAgent')}
              </h3>
              <div className="relative">
                {selectedHumanAgent ? (
                  <div className="flex items-center gap-sm p-sm rounded-lg border border-secondary/30 bg-secondary/5">
                    <div className="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-semibold text-sm">
                      {selectedHumanAgent.username?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className="font-label-md text-label-md text-on-surface truncate">{selectedHumanAgent.username}</span>
                      {selectedHumanAgent.email && <span className="font-body-sm text-body-sm text-on-surface-variant truncate">{selectedHumanAgent.email}</span>}
                    </div>
                    <button
                      onClick={() => { setHumanAgentId(''); setHumanAgentDropdownOpen(false); }}
                      className="ml-auto text-on-surface-variant hover:text-error transition-colors p-xs rounded-full hover:bg-error/10"
                    >
                      <span className="material-symbols-outlined text-[16px]">close</span>
                    </button>
                  </div>
                ) : (
                  <button
                    className="flex items-center justify-between w-full p-sm border border-dashed border-outline-variant bg-surface-container-lowest rounded-lg hover:border-secondary/40 transition-colors focus:border-secondary focus:ring-2 focus:ring-secondary/20"
                    onClick={() => setHumanAgentDropdownOpen(!humanAgentDropdownOpen)}
                  >
                    <span className="font-body-sm text-body-sm text-on-surface-variant">{t('humanAgentPlaceholder')}</span>
                    <span className="material-symbols-outlined text-on-surface-variant text-[18px]">expand_more</span>
                  </button>
                )}
                {humanAgentDropdownOpen && (
                  <div className="absolute z-20 mt-1 w-full bg-surface-container-lowest border border-outline-variant rounded-lg shadow-lg max-h-48 overflow-auto">
                    {humanAgents.length === 0 ? (
                      <div className="p-3 text-on-surface-variant font-body-sm text-body-sm text-center">{t('noHumanAgents')}</div>
                    ) : (
                      humanAgents.map((ha) => (
                        <button
                          key={ha.id}
                          className={`w-full flex items-center gap-sm p-sm hover:bg-surface-container transition-colors text-left rounded-md ${
                            humanAgentId === ha.id ? 'bg-secondary/10' : ''
                          }`}
                          onClick={() => {
                            setHumanAgentId(ha.id);
                            setHumanAgentDropdownOpen(false);
                          }}
                        >
                          <div className="w-7 h-7 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-semibold text-xs">
                            {ha.username?.[0]?.toUpperCase() || '?'}
                          </div>
                          <div className="flex flex-col min-w-0">
                            <span className="font-body-sm text-body-sm text-on-surface font-medium truncate">{ha.username}</span>
                            {ha.email && <span className="font-body-sm text-body-sm text-on-surface-variant truncate">{ha.email}</span>}
                          </div>
                          {humanAgentId === ha.id && (
                            <span className="ml-auto material-symbols-outlined text-secondary text-[16px]">check_circle</span>
                          )}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="col-span-4 flex flex-col gap-lg">
        <div className="bg-card-bg rounded-xl p-lg shadow-soft flex flex-col gap-md border border-outline-variant">
          <h3 className="font-h3 text-h3 text-on-surface border-b border-outline-variant pb-sm mb-sm">{t('status')}</h3>
          <div className="flex justify-between items-center">
            <div className="flex flex-col">
              <span className="font-label-md text-label-md text-on-surface">{t('enableAgent')}</span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">{t('enableDesc')}</span>
            </div>
            <button
              onClick={handleToggle}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-light focus:ring-offset-2 ${isEnabled ? 'bg-primary' : 'bg-surface-variant'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-surface-container-lowest transition-transform ${isEnabled ? 'translate-x-6' : 'translate-x-1'}`}></span>
            </button>
          </div>
          <div className="flex justify-between items-center mt-md pt-md border-t border-outline-variant">
            <span className="font-body-sm text-body-sm text-on-surface-variant">{t('lastUpdated')}</span>
            <span className="font-body-sm text-body-sm text-on-surface">
              {lastUpdated ? new Date(lastUpdated).toLocaleString() : '-'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-sm">
          <div className="bg-surface-container-low rounded-xl p-md flex flex-col gap-xs">
            <span className="material-symbols-outlined text-primary mb-xs">call_split</span>
            <span className="font-label-sm text-label-sm text-on-surface-variant">{t('totalRoutes')}</span>
            <span className="font-h2 text-h2 text-on-surface">-</span>
          </div>
          <div className="bg-surface-container-low rounded-xl p-md flex flex-col gap-xs">
            <span className="material-symbols-outlined text-success mb-xs">check_circle</span>
            <span className="font-label-sm text-label-sm text-on-surface-variant">{t('successRate')}</span>
            <span className="font-h2 text-h2 text-on-surface">-</span>
          </div>
        </div>
      </div>
    </div>
  );
});

export default GeneralInfoTab;
