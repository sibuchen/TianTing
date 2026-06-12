'use client';
 
import React, { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { toolsApi } from '@/lib/api';
import { message } from 'antd';

interface BuiltinTool {
  id: string;
  name: string;
  nameEn: string | null;
  icon: string;
  description: string;
  category: string;
  categoryLabel: string;
  categoryIcon: string;
  isEnabled: boolean;
}

export default function BuiltInToolsTab() {
  const t = useTranslations('Tools.builtin');
  const [tools, setTools] = useState<BuiltinTool[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      setLoading(true);
      const res: any = await toolsApi.listBuiltin();
      const data = res?.data ?? res;
      const items = Array.isArray(data) ? data : [];
      setTools(items);
    } catch {
      setTools([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = async (id: string) => {
    const tool = tools.find(t => t.id === id);
    if (!tool) return;
    const newEnabled = !tool.isEnabled;
    setTools(prev => prev.map(t =>
      t.id === id ? { ...t, isEnabled: newEnabled } : t
    ));
    try {
      await toolsApi.toggleBuiltinTool(id, newEnabled);
    } catch {
      setTools(prev => prev.map(t =>
        t.id === id ? { ...t, isEnabled: !newEnabled } : t
      ));
      message.error(t('toggleFailed') || 'Failed to update tool status');
    }
  };

  const categories = Array.from(new Set(tools.map(t => t.category)));

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-lg">
      {categories.map((category) => {
        const categoryTools = tools.filter(t => t.category === category);
        const categoryLabel = categoryTools[0]?.categoryLabel || category;
        const categoryIcon = categoryTools[0]?.categoryIcon || 'build';
        return (
          <div key={category} className="bg-card-bg rounded-xl border border-outline-variant shadow-soft overflow-hidden">
            <div className="px-md py-4 border-b border-outline-variant bg-surface-bright flex justify-between items-center">
              <div>
                <h3 className="font-h3 text-h3 text-on-surface">{categoryLabel}</h3>
              </div>
              <div className="bg-primary-light text-primary px-3 py-1 rounded-full font-label-sm text-label-sm flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-primary inline-block"></span>
                {categoryTools.filter(t => t.isEnabled).length} {t('active')}
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
                  {categoryTools.map((tool) => (
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
}
