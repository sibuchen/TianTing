'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { App, Modal, Form, Input, Select, Popconfirm, Upload, Tag, Button, AutoComplete } from 'antd';
import { FluidDropdown } from '@/components/ui/fluid-dropdown';
import { Filter, CheckCircle2, XCircle, List, Upload as UploadIcon, Download } from 'lucide-react';
import { skillsApi } from '@/lib/api';

const { TextArea } = Input;

const TAG_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

function getTagColor(index: number): string {
  return TAG_COLORS[index % TAG_COLORS.length];
}

const NAME_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export default function SkillsPage() {
  const { message } = App.useApp();
  const t = useTranslations('Skills');
  const [status, setStatus] = useState('all');
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [editSkill, setEditSkill] = useState<any>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const [tags, setTags] = useState<string[]>([]);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [searchText, setSearchText] = useState('');
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [detailSkill, setDetailSkill] = useState<any>(null);

  const fetchSkills = useCallback((params?: Record<string, unknown>) => {
    setLoading(true);
    skillsApi.list(params)
      .then((res: any) => {
        const data = res?.data ?? res;
        setSkills(Array.isArray(data) ? data : data?.items ?? []);
      })
      .catch(() => {
        setSkills([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const fetchTags = useCallback(() => {
    skillsApi.getTags()
      .then((res: any) => {
        const data = res?.data ?? res;
        setTags(Array.isArray(data) ? data : data?.tags ?? []);
      })
      .catch(() => {
        setTags([]);
      });
  }, []);

  useEffect(() => {
    fetchSkills();
    fetchTags();
  }, [fetchSkills, fetchTags]);

  const handleTagFilter = (tag: string | null) => {
    setActiveTag(tag);
    const params: Record<string, unknown> = {};
    if (tag) {
      params.tags = tag;
    }
    if (searchText) {
      params.search = searchText;
    }
    fetchSkills(params);
  };

  const handleSearch = (value: string) => {
    setSearchText(value);
    if (searchTimer.current) {
      clearTimeout(searchTimer.current);
    }
    searchTimer.current = setTimeout(() => {
      const params: Record<string, unknown> = {};
      if (activeTag) {
        params.tags = activeTag;
      }
      if (value) {
        params.search = value;
      }
      fetchSkills(params);
    }, 300);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (searchTimer.current) {
        clearTimeout(searchTimer.current);
      }
      const params: Record<string, unknown> = {};
      if (activeTag) {
        params.tags = activeTag;
      }
      if (searchText) {
        params.search = searchText;
      }
      fetchSkills(params);
    }
  };

  const handleCreate = () => {
    setEditSkill(null);
    form.resetFields();
    form.setFieldsValue({ category: 'general' });
    setCreateOpen(true);
  };

  const handleEdit = (skill: any) => {
    setEditSkill(skill);
    form.setFieldsValue({
      name: skill.name,
      displayName: skill.displayName || skill.display_name,
      description: skill.description,
      category: skill.category || 'general',
      tags: skill.tags || [],
      skillBody: skill.skillBody || skill.skill_body,
      version: skill.version,
      author: skill.author,
    });
    setCreateOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const payload = {
        ...values,
        category: values.category || 'general',
      };
      if (editSkill) {
        await skillsApi.update(editSkill.id, payload);
        message.success(t('updateSuccess') || 'Updated');
      } else {
        await skillsApi.create(payload);
        message.success(t('createSuccess') || 'Created');
      }
      setCreateOpen(false);
      const params: Record<string, unknown> = {};
      if (activeTag) params.tags = activeTag;
      if (searchText) params.search = searchText;
      fetchSkills(params);
    } catch (error: any) {
      if (error?.errorFields) return;
      const detail = error?.response?.data?.detail;
      if (detail) {
        const messages = Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join('; ')
          : String(detail);
        message.error(messages || t('saveFailed'));
      } else {
        message.error(t('saveFailed') || 'Save failed');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (skillId: string) => {
    try {
      await skillsApi.delete(skillId);
      message.success(t('deleteSuccess') || 'Deleted');
      const params: Record<string, unknown> = {};
      if (activeTag) params.tags = activeTag;
      if (searchText) params.search = searchText;
      fetchSkills(params);
    } catch (error: any) {
      const status = error?.response?.status;
      const data = error?.response?.data;
      if (status === 409 && data?.code === 25003) {
        message.error(t('deleteInUse') || '该技能正在被智能体使用，无法删除');
      } else if (status === 403 && data?.code === 25002) {
        message.error(t('deleteBuiltin') || '内置技能不可删除');
      } else {
        message.error(t('deleteFailed') || 'Delete failed');
      }
    }
  };

  const handleViewDetail = (skill: any) => {
    setDetailSkill(skill);
    setDetailVisible(true);
  };

  const handleExport = async (skillId: string) => {
    try {
      const res: any = await skillsApi.export(skillId);
      const blob = res instanceof Blob ? res : new Blob([res]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const disposition = (res as any)?.headers?.['content-disposition'];
      let filename = `skill-${skillId}.zip`;
      if (disposition) {
        const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '');
        }
      }
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      message.success(t('exportSuccess') || 'Exported');
    } catch {
      message.error(t('saveFailed') || 'Export failed');
    }
  };

  const handleImport = async () => {
    if (!importFile) {
      message.warning(t('selectFile') || 'Please select a .zip file');
      return;
    }
    setImporting(true);
    try {
      await skillsApi.import(importFile);
      message.success(t('importSuccess') || 'Imported');
      setImportOpen(false);
      setImportFile(null);
      const params: Record<string, unknown> = {};
      if (activeTag) params.tags = activeTag;
      if (searchText) params.search = searchText;
      fetchSkills(params);
    } catch (error: any) {
      const status = error?.response?.status;
      if (status === 409) {
        message.error(t('importConflict') || '该技能已存在（名称冲突），请先删除已有技能或修改 SKILL.md 中的 name');
      } else {
        const detail = error?.response?.data?.detail;
        if (detail) {
          const messages = Array.isArray(detail)
            ? detail.map((d: any) => d.msg).join('; ')
            : String(detail);
          message.error(messages || t('importFailed'));
        } else {
          message.error(t('importFailed') || 'Import failed');
        }
      }
    } finally {
      setImporting(false);
    }
  };

  const formatFileSize = (bytes: number | null): string => {
    if (bytes === null || bytes === undefined) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <>
      <div className="max-w-6xl mx-auto p-6">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <div className="page-title-enter">
              <h2 className="text-2xl font-semibold text-on-surface">{t('title')}</h2>
              <p className="text-sm text-on-surface-variant mt-1">{t('subtitle')}</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setImportOpen(true)}
                className="px-4 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface-variant hover:bg-surface-variant hover:scale-[1.02] transition-all duration-200 text-sm font-medium flex items-center gap-2"
              >
                <UploadIcon size={16} />
                {t('importSkill')}
              </button>
              <button
                onClick={handleCreate}
                className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-primary-container hover:scale-[1.02] transition-all shadow-sm"
              >
                <span className="material-symbols-outlined text-[20px]">add</span>
                {t('newSkill')}
              </button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-card-bg p-4 rounded-xl shadow-soft border border-outline-variant">
            <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              <span className="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mr-2">{t('category')}</span>
              <button
                onClick={() => handleTagFilter(null)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
                  activeTag === null
                    ? 'bg-primary text-on-primary'
                    : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-variant border border-outline-variant'
                }`}
              >
                {t('all')}
              </button>
              {tags.map((tag, idx) => (
                <button
                  key={tag}
                  onClick={() => handleTagFilter(tag)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
                    activeTag === tag
                      ? 'bg-primary text-on-primary'
                      : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-variant border border-outline-variant'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative w-full sm:w-48">
                <FluidDropdown
                  value={status}
                  onChange={setStatus}
                  className="w-full"
                  options={[
                    { id: 'all', label: t('allStatuses'), icon: List, color: '#94a3b8' },
                    { id: 'active', label: t('active'), icon: CheckCircle2, color: '#10b981' },
                    { id: 'inactive', label: t('inactive'), icon: XCircle, color: '#ef4444' },
                  ]}
                />
              </div>
            </div>
          </div>

          <div className="relative w-full max-w-lg bg-card-bg rounded-xl border border-outline-variant group/search">
            <div className="relative">
              <Input
                placeholder={t('searchPlaceholder')}
                value={searchText}
                onChange={(e) => handleSearch(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                prefix={<span className="material-symbols-outlined text-[18px] text-on-surface-variant">search</span>}
                className="rounded-xl border-0 bg-transparent"
                allowClear
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loading ? (
              <div className="col-span-full text-center py-12 text-on-surface-variant">
                <span className="material-symbols-outlined text-[32px] animate-spin">progress_activity</span>
                <p className="mt-2 text-sm">Loading...</p>
              </div>
            ) : skills.length === 0 ? (
              <div className="col-span-full text-center py-12 text-on-surface-variant">
                <span className="material-symbols-outlined text-[40px]">extension</span>
                <p className="mt-2 text-sm">{t('noSkills') || 'No skills found'}</p>
              </div>
            ) : (
              skills.map((skill) => (
                <div key={skill.id} className="bg-card-bg rounded-[12px] p-6 flex flex-col shadow-soft border border-outline-variant hover:-translate-y-[2px] hover:shadow-lg transition-all duration-300">
                  <div className="flex justify-between items-start mb-4">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: skill.iconColor ? `${skill.iconColor}20` : undefined, color: skill.iconColor }}>
                      <span className="material-symbols-outlined text-[24px]">{skill.icon || 'extension'}</span>
                    </div>
                    {skill.status === 'active' ? (
                      <span className="px-2.5 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed text-xs font-medium flex items-center gap-1.5 border border-secondary-fixed-dim">
                        <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                        {t('active')}
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded-full bg-surface-variant text-on-surface-variant text-xs font-medium flex items-center gap-1.5 border border-outline-variant">
                        <span className="w-1.5 h-1.5 rounded-full bg-outline"></span>
                        {t('inactive')}
                      </span>
                    )}
                  </div>
                  <h3 className="text-xl font-semibold text-on-surface mb-1">{skill.displayName || skill.display_name || skill.name}</h3>
                  <span className="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-3">{skill.name}</span>
                  <p className="text-sm text-on-surface-variant line-clamp-2 mb-3">{skill.description}</p>
                  {skill.tags && skill.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {skill.tags.map((tag: string, idx: number) => (
                        <Tag key={tag} color={getTagColor(idx)} className="text-[11px] m-0 px-1.5 py-0 leading-5 rounded-full border-0">
                          {tag}
                        </Tag>
                      ))}
                    </div>
                  )}
                  <div className="flex-1" />
                  <div className="pt-4 flex justify-between items-center mt-auto">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(skill)}
                        className="text-on-surface-variant hover:text-primary transition-colors p-1.5 rounded-md hover:bg-surface-variant"
                      >
                        <span className="material-symbols-outlined text-[20px]">edit</span>
                      </button>
                      <button
                        onClick={() => handleViewDetail(skill)}
                        className="text-on-surface-variant hover:text-primary transition-colors p-1.5 rounded-md hover:bg-surface-variant"
                        title={t('viewDetails')}
                      >
                        <span className="material-symbols-outlined text-[20px]">info</span>
                      </button>
                      <button
                        onClick={() => handleExport(skill.id)}
                        className="text-on-surface-variant hover:text-primary transition-colors p-1.5 rounded-md hover:bg-surface-variant"
                        title={t('export')}
                      >
                        <Download size={18} />
                      </button>
                    </div>
                    <Popconfirm
                      title={t('confirmDelete') || 'Delete this skill?'}
                      onConfirm={() => handleDelete(skill.id)}
                      okText={t('yes') || 'Yes'}
                      cancelText={t('no') || 'No'}
                    >
                      <button className="text-on-surface-variant hover:text-error transition-colors p-1.5 rounded-md hover:bg-error-container">
                        <span className="material-symbols-outlined text-[20px]">delete</span>
                      </button>
                    </Popconfirm>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <Modal
        title={t('resourceDetails')}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={
          <button
            onClick={() => setDetailVisible(false)}
            className="px-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-sm text-text-primary hover:bg-surface-container-high transition-colors"
          >
            {t('close') || '关闭'}
          </button>
        }
        width={640}
        destroyOnClose
      >
        {detailSkill?.resources?.length > 0 ? (
          <div className="space-y-2">
            <div className="grid grid-cols-12 gap-2 pb-2 border-b border-outline-variant text-xs text-text-secondary font-medium">
              <span className="col-span-4">{t('fileName')}</span>
              <span className="col-span-2">{t('fileSize')}</span>
              <span className="col-span-3">{t('fileType')}</span>
              <span className="col-span-3">{t('storageStatus')}</span>
            </div>
            {detailSkill.resources.map((r: any) => (
              <div key={r.id} className="grid grid-cols-12 gap-2 py-2 border-b border-outline-variant/50 text-sm text-text-primary last:border-0">
                <span className="col-span-4 truncate font-mono text-xs" title={r.fileName}>{r.fileName}</span>
                <span className="col-span-2 text-text-secondary">{formatFileSize(r.fileSize)}</span>
                <span className="col-span-3 text-text-secondary text-xs">{r.mimeType || '-'}</span>
                <span className="col-span-3">
                  {r.filePath ? (
                    <span className="inline-flex items-center gap-1 text-xs text-green-600">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                      {t('storageDiskDB')}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs text-blue-600">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                      {t('storageDBOnly')}
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-text-secondary">
            <span className="material-symbols-outlined text-4xl mb-2 block">folder_open</span>
            <p>{t('noResources')}</p>
          </div>
        )}
      </Modal>

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{editSkill ? t('editSkill') || 'Edit Skill' : t('newSkill')}</span>}
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        confirmLoading={saving}
        centered
        width={640}
        footer={null}
      >
        <Form form={form} layout="vertical" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              <Form.Item
                name="name"
                label={t('skillName') || 'Skill Name'}
                extra={t('skillNameHint')}
                rules={[
                  { required: true, message: t('nameRequired') || 'Name is required' },
                  { pattern: NAME_PATTERN, message: t('namePattern') || 'Only lowercase letters, numbers and hyphens' },
                  { max: 64, message: t('nameMaxLength') || 'Name must not exceed 64 characters' },
                ]}
              >
                <Input className="rounded-lg" placeholder="sales-skill" />
              </Form.Item>
              <Form.Item
                name="displayName"
                label={t('displayName') || 'Display Name'}
              >
                <Input className="rounded-lg" />
              </Form.Item>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Form.Item
                name="category"
                label={t('category') || 'Category'}
              >
                <AutoComplete
                  className="rounded-lg w-full"
                  placeholder={t('categoryPlaceholder') || '输入或选择分类'}
                  allowClear
                  options={[
                    { value: 'general', label: t('general') || '通用' },
                    { value: 'sales', label: t('sales') },
                    { value: 'service', label: t('service') },
                    { value: 'logistics', label: t('logistics') },
                  ]}
                />
              </Form.Item>
              <Form.Item
                name="tags"
                label={t('tags') || 'Tags'}
              >
                <Select
                  mode="tags"
                  className="rounded-lg w-full"
                  placeholder="输入标签后按回车添加"
                />
              </Form.Item>
            </div>
            <Form.Item
              name="description"
              label={t('description') || 'Description'}
              rules={[
                { max: 1024, message: t('descriptionMaxLength') || 'Description must not exceed 1024 characters' },
              ]}
            >
              <TextArea rows={3} className="rounded-lg" />
            </Form.Item>
            <Form.Item
              name="skillBody"
              label={t('skillBody') || 'SKILL.md Body'}
            >
              <TextArea rows={8} className="rounded-lg font-mono text-sm" />
            </Form.Item>
            <Form.Item
              name="resources"
              label={t('resources') || 'Resources'}
            >
              <Upload
                multiple
                beforeUpload={(file) => {
                  return false;
                }}
                maxCount={10}
                accept=".md,.py,.txt,.json,.yaml,.yml,.js,.ts"
                listType="text"
              >
                <Button icon={<UploadIcon size={14} />}>{t('uploadResources') || 'Upload Resources'}</Button>
              </Upload>
            </Form.Item>
            <div className="grid grid-cols-2 gap-4">
              <Form.Item
                name="version"
                label={t('version') || 'Version'}
              >
                <Input className="rounded-lg" placeholder="1.0.0" />
              </Form.Item>
              <Form.Item
                name="author"
                label={t('author') || 'Author'}
              >
                <Input className="rounded-lg" />
              </Form.Item>
            </div>
          </Form>
        <div className="flex justify-between items-center mt-6 pt-4 border-t border-white/10">
          <button
            onClick={() => setCreateOpen(false)}
            className="px-5 py-2 rounded-xl text-sm font-medium text-on-surface-variant border border-white/20 hover:bg-white/5 transition-all duration-200"
          >
            {t('cancel') || 'Cancel'}
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className={`px-6 py-2.5 rounded-lg font-medium text-sm flex items-center gap-2 bg-primary text-on-primary hover:bg-primary-container hover:scale-[1.02] transition-all duration-200 ${saving ? 'opacity-80 pointer-events-none' : ''}`}
          >
            {saving && (
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            )}
            {t('save') || 'Save'}
          </button>
        </div>
      </Modal>

      <Modal
        title={<span className="text-lg font-bold text-on-surface">{t('importSkill') || 'Import Skill'}</span>}
        open={importOpen}
        onCancel={() => {
          setImportOpen(false);
          setImportFile(null);
        }}
        onOk={handleImport}
        confirmLoading={importing}
        okText={t('import') || 'Import'}
        cancelText={t('cancel') || 'Cancel'}
        centered
        width={480}
      >
        <div className="mt-4">
          <Upload
            beforeUpload={(file) => {
              setImportFile(file);
              return false;
            }}
            maxCount={1}
            accept=".zip"
            onRemove={() => setImportFile(null)}
          >
            <Button icon={<UploadIcon size={16} />}>{t('selectFile') || 'Select .zip file'}</Button>
          </Upload>
        </div>
      </Modal>

      </>
  );
}