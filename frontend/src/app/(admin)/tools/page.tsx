'use client';
 
import React, { useState, useRef } from 'react';
import BuiltInToolsTab from '@/components/tools/BuiltInToolsTab';
import CustomToolsTab from '@/components/tools/CustomToolsTab';
import MCPServerTab from '@/components/tools/MCPServerTab';
import MCPToolsTab, { type MCPToolsTabHandle } from '@/components/tools/MCPToolsTab';
import { useTranslations } from 'next-intl';
import { SlidingSwitch } from '@/components/ui/SlidingSwitch';

export default function ToolsPage() {
  const t = useTranslations('Tools');
  const [activeTab, setActiveTab] = useState('builtin');
  const [refreshKey, setRefreshKey] = useState(0);
  const mcpToolsTabRef = useRef<MCPToolsTabHandle>(null);

  const handleMcpServerChange = () => {
    mcpToolsTabRef.current?.refresh();
    setRefreshKey(prev => prev + 1);
  };


  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="space-y-8">
        {/* Page Header Area */}
        <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-on-surface">{t('title')}</h2>
          <p className="text-sm text-on-surface-variant mt-1">{t('subtitle')}</p>
        </div>
      </div>

      {/* Custom Tabs Implementation (Matching Agent Edit Page style) */}
      <SlidingSwitch 
        value={activeTab}
        onChange={setActiveTab}
        options={[
          { label: t('builtinTab'), value: 'builtin' },
          { label: t('customTab'), value: 'custom' },
          { label: t('mcpTab'), value: 'mcp' },
          { label: t('mcpToolsTab'), value: 'mcptools' },
        ]}
      />

      {/* Content Area */}
      <div className="pt-2">
        <div className={activeTab === 'builtin' ? '' : 'hidden'}>
          <BuiltInToolsTab />
        </div>
        <div className={activeTab === 'custom' ? '' : 'hidden'}>
          <CustomToolsTab />
        </div>
        <div className={activeTab === 'mcp' ? '' : 'hidden'}>
          <MCPServerTab onServerChange={handleMcpServerChange} />
        </div>
        <div className={activeTab === 'mcptools' ? '' : 'hidden'}>
          <MCPToolsTab ref={mcpToolsTabRef} activeTab={activeTab} refreshKey={refreshKey} />
        </div>
      </div>
      </div>
    </div>
  );
}

