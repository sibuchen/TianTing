'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { settingsApi, agentsApi } from '@/lib/api';

interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  modelId: string;
  baseUrl: string;
  capabilities: string[];
  verified?: boolean;
}

export interface ModelBindingTabHandle {
  save: () => Promise<boolean>;
  isDirty: () => boolean;
}

const ModelBindingTab = forwardRef<ModelBindingTabHandle, { agentId: string, agentData?: Record<string, any> }>(function ModelBindingTab({ agentId, agentData }, ref) {
  const t = useTranslations('AgentEdit.model');
  const [modelConfigs, setModelConfigs] = useState<ModelConfig[]>([]);
  const [selectedConfigId, setSelectedConfigId] = useState<string>('');
  const [originalConfigId, setOriginalConfigId] = useState<string>('');
  const [selectedCapability, setSelectedCapability] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [providerOpen, setProviderOpen] = useState(false);
  const [modelOpen, setModelOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const configsRes = await settingsApi.getModelConfigs();
        const configs = Array.isArray(configsRes) ? configsRes : ((configsRes as unknown) as Record<string, unknown>)?.data as ModelConfig[] || ((configsRes as unknown) as Record<string, unknown>)?.items as ModelConfig[] || [];
        setModelConfigs(configs);
        
        if (agentData) {
          const modelInfo = (agentData?.modelInfo || agentData?.model_info) as Record<string, string> | undefined;
          const initialId = modelInfo?.id || (agentData?.modelConfigId as string) || (configs.length > 0 ? configs[0].id : '');
          setSelectedConfigId(initialId);
          setOriginalConfigId(initialId);
          const config = configs.find((c: ModelConfig) => c.id === initialId);
          if (config && config.capabilities && config.capabilities.length > 0) {
            setSelectedCapability(config.capabilities[0]);
          }
        }
      } catch {
        setModelConfigs([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [agentData]);

  const selectedConfig = modelConfigs.find(c => c.id === selectedConfigId);

  const handleSelectProvider = (configId: string) => {
    setSelectedConfigId(configId);
    const config = modelConfigs.find(c => c.id === configId);
    if (config && config.capabilities && config.capabilities.length > 0) {
      setSelectedCapability(config.capabilities[0]);
    }
    setProviderOpen(false);
  };

  const handleSelectModel = (modelId: string) => {
    setSelectedCapability(modelId);
    setModelOpen(false);
  };

  const handleSave = async (): Promise<boolean> => {
    console.log('[ModelBindingTab] handleSave called', { agentId, selectedConfigId, originalConfigId, isEqual: selectedConfigId === originalConfigId });
    if (!agentId) { console.log('[ModelBindingTab] no agentId, skip'); return true; }
    if (selectedConfigId === originalConfigId) { console.log('[ModelBindingTab] no change, skip'); return true; }
    try {
      console.log('[ModelBindingTab] calling API update', { modelConfigId: selectedConfigId || null });
      await agentsApi.update(agentId, { modelConfigId: selectedConfigId || null });
      setOriginalConfigId(selectedConfigId);
      console.log('[ModelBindingTab] save success');
      return true;
    } catch (e) {
      console.log('[ModelBindingTab] save error', e);
      return false;
    }
  };

  useImperativeHandle(ref, () => ({
    save: handleSave,
    isDirty: () => selectedConfigId !== originalConfigId,
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
      <div className="flex items-start gap-3 p-4 mb-lg rounded-xl bg-surface-container-low border border-primary-light shadow-sm">
        <span className="material-symbols-outlined text-info mt-0.5">lightbulb</span>
        <div>
          <h4 className="font-label-md text-label-md text-on-surface mb-1">{t('recommendation')}</h4>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            {t('recommendationDesc')}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-lg">
        <div className="lg:col-span-5 flex flex-col gap-lg">
          <div className="bg-card-bg rounded-xl shadow-soft border border-outline-variant overflow-hidden flex flex-col hover:-translate-y-[2px] transition-transform duration-200">
            <div className="p-5 border-b border-outline-variant bg-surface-bright">
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-primary text-[20px]">api</span>
                <h3 className="font-h3 text-h3 text-on-surface">{t('selectEngine')}</h3>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant">{t('engineDesc')}</p>
            </div>
            <div className="p-5 flex flex-col gap-4 bg-card-bg">
              <div className="flex flex-col gap-2">
                <label className="font-label-sm text-label-sm text-on-surface-variant">{t('configuredProviders')}</label>
                <div className="relative">
                  <button
                    className="flex items-center justify-between w-full p-3 border-2 border-primary-light bg-surface-container-lowest rounded-lg hover:border-primary transition-colors focus:border-primary focus:ring-2 focus:ring-primary-light"
                    onClick={() => setProviderOpen(!providerOpen)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded bg-on-surface text-surface-container-lowest flex items-center justify-center font-bold text-[10px]">
                        {selectedConfig?.provider?.substring(0, 2).toUpperCase() || 'NA'}
                      </div>
                      <div className="flex flex-col">
                        <span className="font-body-md text-body-md text-on-surface font-medium leading-tight">{selectedConfig?.name || 'Select a provider'}</span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant leading-tight">{selectedConfig?.modelId || ''}</span>
                      </div>
                    </div>
                    <span className="material-symbols-outlined text-on-surface-variant">expand_more</span>
                  </button>
                  {providerOpen && (
                    <div className="absolute z-20 mt-1 w-full bg-surface-container-lowest border border-outline-variant rounded-lg shadow-lg max-h-60 overflow-auto">
                      {modelConfigs.length === 0 ? (
                        <div className="p-3 text-on-surface-variant font-body-sm text-body-sm text-center">{t('noProviders') || 'No providers configured'}</div>
                      ) : (
                        modelConfigs.map((config) => (
                          <button
                            key={config.id}
                            className="w-full flex items-center gap-3 p-3 hover:bg-surface-container transition-colors text-left"
                            onClick={() => handleSelectProvider(config.id)}
                          >
                            <div className="w-6 h-6 rounded bg-on-surface text-surface-container-lowest flex items-center justify-center font-bold text-[10px]">
                              {config.provider?.substring(0, 2).toUpperCase()}
                            </div>
                            <div className="flex flex-col">
                              <span className="font-body-md text-body-md text-on-surface font-medium leading-tight">{config.name}</span>
                              <span className="font-body-sm text-body-sm text-on-surface-variant leading-tight">{config.modelId}</span>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex flex-col gap-2 mt-2">
                <label className="font-label-sm text-label-sm text-on-surface-variant">{t('selectedModel')}</label>
                <div className="relative">
                  <button
                    className="flex items-center justify-between w-full p-3 border border-outline-variant bg-surface-container-lowest rounded-lg hover:border-primary transition-colors"
                    onClick={() => setModelOpen(!modelOpen)}
                  >
                    <span className="font-body-md text-body-md text-on-surface">{selectedCapability || selectedConfig?.modelId || 'Select a model'}</span>
                    <span className="material-symbols-outlined text-on-surface-variant">expand_more</span>
                  </button>
                  {modelOpen && selectedConfig && (
                    <div className="absolute z-20 mt-1 w-full bg-surface-container-lowest border border-outline-variant rounded-lg shadow-lg">
                      {selectedConfig.capabilities?.map((cap) => (
                        <button
                          key={cap}
                          className="w-full flex items-center gap-2 p-3 hover:bg-surface-container transition-colors text-left"
                          onClick={() => handleSelectModel(cap)}
                        >
                          <span className="font-body-md text-body-md text-on-surface">{cap}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between border-t border-outline-variant pt-4">
                <span className="font-body-sm text-body-sm text-on-surface-variant">{t('needNewProvider')}</span>
                <Link href="/api-keys" className="font-label-sm text-label-sm text-primary hover:text-primary-container flex items-center gap-1 transition-colors">
                  {t('goToApiKeys')} <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </Link>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-7">
          <div className="bg-card-bg rounded-xl shadow-soft border border-outline-variant h-full flex flex-col hover:-translate-y-[2px] transition-transform duration-200">
            <div className="p-5 border-b border-outline-variant bg-surface-bright flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-success text-[20px]">check_circle</span>
                <h3 className="font-h3 text-h3 text-on-surface">{t('configDetails')}</h3>
              </div>
              {selectedConfig && (
                <span className="px-2.5 py-1 rounded-full bg-secondary-container text-on-secondary-container font-label-sm text-label-sm border border-secondary-fixed">{t('activeTarget')}</span>
              )}
            </div>
            <div className="p-6 bg-card-bg flex-1">
              {selectedConfig ? (
                <div className="grid grid-cols-2 gap-x-8 gap-y-6">
                  <div className="flex flex-col gap-1 border-b border-surface-container pb-4 col-span-2 md:col-span-1">
                    <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{t('provider')}</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="font-body-lg text-body-lg text-on-surface font-medium">{selectedConfig.provider}</span>
                      {selectedConfig.verified && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-surface-container-high text-on-surface-variant border border-outline-variant">{t('verified')}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col gap-1 border-b border-surface-container pb-4 col-span-2 md:col-span-1">
                    <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{t('modelId')}</span>
                    <span className="font-code text-code text-on-surface bg-surface-container-low px-2 py-1 rounded w-fit mt-1 border border-outline-variant">{selectedConfig.modelId}</span>
                  </div>
                  <div className="flex flex-col gap-1 border-b border-surface-container pb-4 col-span-2">
                    <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{t('baseUrl')}</span>
                    <div className="flex items-center gap-2 mt-1 bg-surface-container-lowest border border-outline-variant p-2 rounded-lg">
                      <span className="material-symbols-outlined text-on-surface-variant text-[16px]">link</span>
                      <span className="font-code text-code text-on-surface-variant truncate">{selectedConfig.baseUrl}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 col-span-2 mt-2">
                    <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider mb-1">{t('capabilities')}</span>
                    <div className="flex flex-wrap gap-2">
                      {selectedConfig.capabilities?.map((cap) => (
                        <div key={cap} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-light text-primary border border-primary/20">
                          <span className="material-symbols-outlined text-[16px]">functions</span>
                          <span className="font-label-sm text-label-sm">{cap}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center py-16 text-on-surface-variant font-body-sm text-body-sm">
                  {t('noConfig') || 'No model configuration selected'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

export default ModelBindingTab;
