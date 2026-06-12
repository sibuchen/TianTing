'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle, useMemo } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { App, Tooltip } from 'antd';
import { FluidDropdown } from '@/components/ui/fluid-dropdown';
import { Filter, Tag } from 'lucide-react';
import { skillsApi, agentsApi } from '@/lib/api';

interface SkillResource {
  id: string;
  fileName: string;
  filePath?: string;
  fileSize?: number;
  mimeType?: string;
}

interface Skill {
  id: string;
  name: string;
  displayName?: string;
  category: string;
  description?: string;
  icon?: string;
  iconColor?: string;
  status: string;
  skillBody?: string;
  tags?: string[];
  version?: string;
  author?: string;
  prompts?: string;
  isBuiltin: boolean;
  resources?: SkillResource[];
}

const TAG_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'];

export interface SkillsTabHandle {
  save: () => Promise<boolean>;
  isDirty: () => boolean;
}

const SkillsTab = forwardRef<SkillsTabHandle, { agentId: string, agentData?: Record<string, any> }>(function SkillsTab({ agentId, agentData }, ref) {
  const { message } = App.useApp();
  const t = useTranslations('AgentEdit.skills');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [skills, setSkills] = useState<Skill[]>([]);
  const [assignedSkillIds, setAssignedSkillIds] = useState<string[]>([]);
  const [originalSkillIds, setOriginalSkillIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [skillsRes, tagsRes] = await Promise.all([
          skillsApi.list(),
          skillsApi.getTags().catch(() => []),
        ]);
        setSkills(Array.isArray(skillsRes) ? skillsRes : ((skillsRes as unknown) as Record<string, unknown>)?.data as Skill[] || ((skillsRes as unknown) as Record<string, unknown>)?.items as Skill[] || []);

        const tags = Array.isArray(tagsRes) ? tagsRes : ((tagsRes as unknown) as Record<string, unknown>)?.data as string[] || ((tagsRes as unknown) as Record<string, unknown>)?.tags as string[] || [];
        setAvailableTags(tags);

        if (agentData) {
          const initialIds = Array.isArray(agentData?.skills)
            ? agentData.skills.map((s: Skill | string) => typeof s === 'string' ? s : (s as any).id)
            : [];
          setAssignedSkillIds(initialIds);
          setOriginalSkillIds(initialIds);
        }
      } catch {
        setSkills([]);
        setAssignedSkillIds([]);
        setOriginalSkillIds([]);
        setAvailableTags([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [agentData]);

  const filteredSkills = useMemo(() => {
    return skills.filter(skill => {
      if (filter !== 'all' && !(skill.tags || []).includes(filter)) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const nameMatch = skill.name?.toLowerCase().includes(q);
        const displayNameMatch = skill.displayName?.toLowerCase().includes(q);
        const descMatch = skill.description?.toLowerCase().includes(q);
        if (!nameMatch && !displayNameMatch && !descMatch) {
          return false;
        }
      }
      return true;
    });
  }, [skills, filter, searchQuery]);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleAssign = (skillId: string) => {
    setAssignedSkillIds([...assignedSkillIds, skillId]);
  };

  const handleRemove = (skillId: string) => {
    setAssignedSkillIds(assignedSkillIds.filter(id => id !== skillId));
  };

  const handleSave = async (): Promise<boolean> => {
    if (!agentId) return false;
    const toAdd = assignedSkillIds.filter(id => !originalSkillIds.includes(id));
    const toRemove = originalSkillIds.filter(id => !assignedSkillIds.includes(id));
    if (toAdd.length === 0 && toRemove.length === 0) return true;
    try {
      for (const skillId of toAdd) {
        await agentsApi.assignSkill(agentId, skillId);
      }
      for (const skillId of toRemove) {
        await agentsApi.removeSkill(agentId, skillId);
      }
      setOriginalSkillIds([...assignedSkillIds]);
      return true;
    } catch {
      message.error(t('assignFailed') || '技能保存失败');
      return false;
    }
  };

  useImperativeHandle(ref, () => ({
    save: handleSave,
    isDirty: () => {
      const toAdd = assignedSkillIds.filter(id => !originalSkillIds.includes(id));
      const toRemove = originalSkillIds.filter(id => !assignedSkillIds.includes(id));
      return toAdd.length > 0 || toRemove.length > 0;
    },
  }));

  const assignedSkills = skills.filter(s => assignedSkillIds.includes(s.id));

  const filterOptions = useMemo(() => {
    const options: { id: string; label: string; icon: any; color: string }[] = [
      { id: 'all', label: t('filter') || 'All Categories', icon: Filter, color: '#94a3b8' },
    ];
    availableTags.forEach((tag, idx) => {
      options.push({
        id: tag,
        label: tag,
        icon: Tag,
        color: TAG_COLORS[idx % TAG_COLORS.length],
      });
    });
    return options;
  }, [availableTags, t]);

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-lg items-start">
      <div className="md:col-span-4 flex flex-col gap-lg">
        <div className="bg-card-bg rounded-xl ambient-shadow p-lg border border-outline-variant">
          <div className="flex items-center justify-between mb-md">
            <h2 className="font-h3 text-h3 text-on-surface">{t('assignedSkills')}</h2>
            <span className="bg-surface-container text-on-surface-variant px-2 py-0.5 rounded text-label-sm font-label-sm">{t('activeCount', { count: assignedSkills.length })}</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-md">
            {t('assignedDesc')}
          </p>
          <div className="flex flex-wrap gap-sm">
            {assignedSkills.length === 0 && (
              <span className="font-body-sm text-body-sm text-on-surface-variant italic">{t('noAssigned') || 'No skills assigned yet'}</span>
            )}
            {assignedSkills.map((skill) => (
              <Tooltip key={skill.id} title={skill.description || skill.name}>
                <div className="inline-flex items-center gap-sm bg-primary-fixed text-on-primary-fixed-variant px-sm py-xs rounded-lg border border-primary-fixed-dim hover:-translate-y-0.5 transition-transform cursor-default max-w-[220px]">
                  <span className="material-symbols-outlined text-[16px] shrink-0">{skill.icon || 'psychology'}</span>
                  <span className="font-label-md text-label-md truncate">{skill.displayName || skill.name}</span>
                  <button
                    onClick={() => handleRemove(skill.id)}
                    className="ml-auto text-on-primary-fixed-variant/70 hover:text-error transition-colors flex items-center justify-center rounded-full hover:bg-surface-container-high p-0.5 shrink-0"
                  >
                    <span className="material-symbols-outlined text-[14px]">close</span>
                  </button>
                </div>
              </Tooltip>
            ))}
          </div>
        </div>

        <Link
          href="/skills"
          className="border-2 border-dashed border-outline-variant rounded-xl p-lg flex flex-col items-center justify-center text-center bg-surface-container-low min-h-[140px] hover:border-primary/40 hover:bg-surface-container transition-colors group"
        >
          <div className="w-12 h-12 bg-surface-container rounded-full flex items-center justify-center mb-sm text-outline group-hover:text-primary transition-colors">
            <span className="material-symbols-outlined">settings</span>
          </div>
          <h3 className="font-label-md text-label-md text-on-surface mb-xs">{t('manageSkills') || 'Manage Skills'}</h3>
          <p className="font-body-sm text-body-sm text-on-surface-variant max-w-[200px]">{t('manageSkillsDesc') || 'Create, import and manage skills in the library'}</p>
        </Link>
      </div>

      <div className="md:col-span-8 bg-card-bg rounded-xl ambient-shadow border border-outline-variant flex flex-col overflow-hidden">
        <div className="p-lg border-b border-outline-variant bg-surface-container-low">
          <div className="flex items-center justify-between mb-md">
            <h2 className="font-h3 text-h3 text-on-surface">{t('availableLibrary')}</h2>
          </div>
          <div className="flex gap-md items-center">
            <div className="relative flex-1">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">search</span>
              <input
                className="w-full pl-10 pr-4 py-2 bg-background border border-outline-variant rounded-lg font-body-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                placeholder={t('searchPlaceholder')}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <FluidDropdown
              value={filter}
              onChange={setFilter}
              className="w-44"
              options={filterOptions}
            />
          </div>
        </div>

        <div className="flex-1 overflow-auto max-h-[600px]">
          <div className="grid grid-cols-12 gap-md px-lg py-sm bg-surface-container-low border-b border-outline-variant text-on-surface-variant font-label-sm text-label-sm sticky top-0 z-10">
            <div className="col-span-6">{t('skillName')}</div>
            <div className="col-span-4">{t('category')}</div>
            <div className="col-span-2 text-right">{t('action')}</div>
          </div>

          {filteredSkills.length === 0 ? (
            <div className="flex items-center justify-center py-16 text-on-surface-variant font-body-sm text-body-sm">
              {searchQuery.trim() || filter !== 'all'
                ? (t('noSearchResults') || 'No matching skills found')
                : (t('noSkills') || 'No skills available')}
            </div>
          ) : (
            filteredSkills.map((skill) => {
              const isExpanded = expandedId === skill.id;
              const isAssigned = assignedSkillIds.includes(skill.id);
              return (
                <div key={skill.id} className="border-b border-outline-variant hover:bg-surface-container-low transition-colors group cursor-pointer">
                  <div
                    className="grid grid-cols-12 gap-md px-lg py-md items-center"
                    onClick={() => toggleExpand(skill.id)}
                  >
                    <div className="col-span-6 flex items-center gap-sm min-w-0">
                      <div className="w-8 h-8 rounded flex items-center justify-center shrink-0"
                        style={{
                          backgroundColor: skill.iconColor ? `${skill.iconColor}20` : undefined,
                          color: skill.iconColor || undefined,
                        }}
                      >
                        <span className="material-symbols-outlined text-[18px]">{skill.icon || 'psychology'}</span>
                      </div>
                      <div className="min-w-0">
                        <div className="font-label-md text-label-md text-on-surface group-hover:text-primary transition-colors flex items-center gap-xs">
                          <span className="truncate">{skill.displayName || skill.name}</span>
                          <span className={`material-symbols-outlined text-[16px] text-on-surface-variant transition-transform shrink-0 ${isExpanded ? 'rotate-180' : ''}`}>
                            expand_more
                          </span>
                        </div>
                        {skill.description && (
                          <p className="font-body-xs text-body-xs text-on-surface-variant truncate mt-0.5">{skill.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="col-span-4 flex items-center flex-wrap gap-1">
                      <span className="px-2 py-1 bg-surface-container rounded text-on-surface-variant font-label-sm text-label-sm">{skill.category}</span>
                      {skill.isBuiltin && (
                        <span className="px-1.5 py-0.5 bg-info/10 text-info rounded text-label-xs font-label-xs">built-in</span>
                      )}
                    </div>
                    <div className="col-span-2 flex justify-end">
                      {isAssigned ? (
                        <span className="px-sm py-1.5 text-on-surface-variant font-label-sm text-label-sm">{t('assigned') || 'Assigned'}</span>
                      ) : (
                        <button
                          className="px-sm py-1.5 border border-primary text-primary rounded font-label-sm text-label-sm hover:bg-primary hover:text-on-primary transition-colors focus:ring-2 focus:ring-primary/20"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAssign(skill.id);
                          }}
                        >
                          {t('assign')}
                        </button>
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="px-lg pb-md pt-xs">
                      <div className="bg-background border border-outline-variant rounded-lg p-md">
                        <div className="flex items-start justify-between mb-sm">
                          <div>
                            <h4 className="font-label-lg text-label-lg text-on-surface">{skill.displayName || skill.name}</h4>
                            {skill.description && (
                              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{skill.description}</p>
                            )}
                          </div>
                          {(skill.version || skill.author) && (
                            <div className="flex items-center gap-sm text-on-surface-variant font-label-xs text-label-xs shrink-0 ml-md">
                              {skill.version && <span>v{skill.version}</span>}
                              {skill.version && skill.author && <span>·</span>}
                              {skill.author && <span>{skill.author}</span>}
                            </div>
                          )}
                        </div>

                        {(skill.skillBody || skill.prompts) && (
                          <div className="mb-sm">
                            <h5 className="font-label-sm text-label-sm text-on-surface-variant mb-xs uppercase tracking-wider">{t('skillContent') || 'Skill Content'}</h5>
                            <pre className="bg-surface-container-low p-sm rounded border border-outline-variant/30 font-code text-code text-on-surface overflow-x-auto max-h-[300px] overflow-y-auto whitespace-pre-wrap break-words text-xs leading-relaxed">
                              {skill.skillBody || skill.prompts}
                            </pre>
                          </div>
                        )}

                        {skill.tags && skill.tags.length > 0 && (
                          <div className="mb-sm">
                            <h5 className="font-label-sm text-label-sm text-on-surface-variant mb-xs uppercase tracking-wider">{t('tags') || 'Tags'}</h5>
                            <div className="flex flex-wrap gap-1">
                              {skill.tags.map((tag, idx) => (
                                <span
                                  key={tag}
                                  className="inline-flex items-center px-2 py-0.5 rounded-full text-label-xs font-label-xs"
                                  style={{
                                    backgroundColor: `${TAG_COLORS[idx % TAG_COLORS.length]}20`,
                                    color: TAG_COLORS[idx % TAG_COLORS.length],
                                    border: `1px solid ${TAG_COLORS[idx % TAG_COLORS.length]}40`,
                                  }}
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {skill.resources && skill.resources.length > 0 && (
                          <div>
                            <h5 className="font-label-sm text-label-sm text-on-surface-variant mb-xs uppercase tracking-wider">{t('resources') || 'Resources'}</h5>
                            <div className="flex flex-wrap gap-sm">
                              {skill.resources.map((res) => (
                                <span key={res.id} className="inline-flex items-center gap-1 px-2 py-1 bg-surface-container rounded text-label-xs font-label-xs text-on-surface-variant">
                                  <span className="material-symbols-outlined text-[14px]">description</span>
                                  {res.fileName}
                                  {res.fileSize != null && <span className="text-on-surface-variant/60">({formatFileSize(res.fileSize)})</span>}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
});

export default SkillsTab;