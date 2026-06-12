'use client';
 
import React from 'react';
import { useTranslations } from 'next-intl';

export default function CustomToolsTab() {
  const t = useTranslations('Tools.custom');

  return (
    <div className="flex flex-col gap-lg">
      <div className="rounded-xl border-2 border-dashed border-outline-variant bg-surface-container-low p-xl flex flex-col items-center justify-center text-center min-h-[400px] hover:border-primary transition-colors hover:bg-surface-bg-light">
        <div className="w-16 h-16 rounded-full bg-primary-light flex items-center justify-center text-primary mb-4 shrink-0">
          <span className="material-symbols-outlined !text-[32px]">extension</span>
        </div>
        <h3 className="font-h3 text-h3 text-on-surface mb-2">{t('title')}</h3>
        <p className="font-body-md text-body-md text-on-surface-variant max-w-[400px] w-full mx-auto mb-6">
          {t('desc')}
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-surface-variant rounded-full text-on-surface font-label-sm text-label-sm font-medium">
          <span className="material-symbols-outlined !text-[18px]">schedule</span>
          <span>{t('comingSoon')}</span>
        </div>
      </div>
    </div>
  );
}
