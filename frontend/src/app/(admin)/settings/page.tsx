'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useSettingStore } from '@/store/settingStore';
import { useAuthStore } from '@/store/authStore';
import { App } from 'antd';
import { useTranslations } from 'next-intl';
import { FluidDropdown } from '@/components/ui/fluid-dropdown';
import { SlidingSwitch } from '@/components/ui/SlidingSwitch';
import { Languages, Globe } from 'lucide-react';
import BrandLogo from '@/app/sibuchen.png';
import { settingsApi } from '@/lib/api';
import AvatarCropper from '@/components/ui/AvatarCropper';

export default function SettingsPage() {
  const { message } = App.useApp();
  const { theme, setTheme, locale, setLocale } = useSettingStore();
  const { updateAvatar } = useAuthStore();
  const t = useTranslations('Settings');
  const tc = useTranslations('Common');

  const [settings, setSettings] = useState<any[]>([]);
  const [modelConfigs, setModelConfigs] = useState<any[]>([]);
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [userInfo, setUserInfo] = useState<{ id: string; username: string; email: string; avatar: string | null } | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [cropperImage, setCropperImage] = useState<string | null>(null);
  const [showCropper, setShowCropper] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([
      settingsApi.get(),
      settingsApi.getModelConfigs(),
      settingsApi.getMCPServers(),
    ])
      .then(([settingsRes, modelConfigsRes, mcpServersRes]: any[]) => {
        setSettings(settingsRes?.data ?? settingsRes ?? []);
        setModelConfigs(modelConfigsRes?.data ?? modelConfigsRes ?? []);
        setMcpServers(mcpServersRes?.data ?? mcpServersRes ?? []);

        const settingsData = settingsRes?.data;
        if (settingsData?.user) {
          setUserInfo(settingsData.user);
        }
      })
      .catch(() => {
        setSettings([]);
        setModelConfigs([]);
        setMcpServers([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleSave = async () => {
    try {
      await settingsApi.update({ theme, locale });
      message.success(t('saved'));
    } catch {
      message.error(t('saveFailed') || 'Save failed');
    }
  };

  const handleCheckUpdate = async () => {
    try {
      const res = await settingsApi.checkUpdate();
      const data = (res as any)?.data;
      if (data?.hasUpdate) {
        message.info(t('updateAvailable') || `New version ${data.latestVersion} available`);
      } else {
        message.success(t('upToDate') || 'Already up to date');
      }
    } catch {
      message.error(t('checkFailed') || 'Check failed');
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      message.error(t('invalidImageType') || '仅支持 JPG、PNG、GIF、WebP 格式');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      message.error(t('imageTooLarge') || '图片大小不能超过 5MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setCropperImage(reader.result as string);
      setShowCropper(true);
    };
    reader.readAsDataURL(file);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCropConfirm = async (blob: Blob) => {
    setShowCropper(false);
    setCropperImage(null);
    setAvatarUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', blob, 'avatar.jpg');
      const res: any = await settingsApi.uploadAvatar(formData);
      const avatarUrl = res?.data?.avatar || res?.avatar;
      if (avatarUrl) {
        setUserInfo((prev) => prev ? { ...prev, avatar: avatarUrl } : null);
        updateAvatar(avatarUrl);
        message.success(t('avatarUploaded') || '头像上传成功');
      }
    } catch {
      message.error(t('avatarUploadFailed') || '头像上传失败');
    } finally {
      setAvatarUploading(false);
    }
  };

  const handleCropCancel = () => {
    setShowCropper(false);
    setCropperImage(null);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-on-surface">{t('title')}</h2>
          <p className="text-sm text-on-surface-variant mt-1">{t('subtitle')}</p>
        </div>
        <button
          onClick={handleSave}
          className="bg-primary text-on-primary px-6 py-2 rounded-lg text-sm font-medium hover:bg-primary-container hover:scale-[1.02] transition-all shadow-sm"
        >
          {tc('save')}
        </button>
      </div>

      <div className="space-y-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
          </div>
        ) : (
        <>
        {/* Account Settings Card */}
        <div className="bg-card-bg rounded-xl p-lg shadow-soft border border-border mb-lg hover:-translate-y-[2px] transition-transform duration-200">
          <div className="flex items-center gap-sm mb-md">
            <span className="material-symbols-outlined text-primary">account_circle</span>
            <h3 className="text-xl font-semibold text-on-surface">{t('accountSettings')}</h3>
          </div>
          <div className="flex flex-col md:flex-row gap-xl items-start">
            <div className="flex-shrink-0">
              <div className="relative group">
                <div className="w-24 h-24 rounded-full overflow-hidden border-2 border-primary/20 shadow-sm">
                  {userInfo?.avatar ? (
                    <img
                      alt="Profile Avatar"
                      className="w-full h-full object-cover"
                      src={userInfo.avatar}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-surface-bg">
                      <span className="material-symbols-outlined text-4xl text-on-surface-variant">person</span>
                    </div>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  className="hidden"
                  onChange={handleAvatarChange}
                />
                <button
                  onClick={handleAvatarClick}
                  disabled={avatarUploading}
                  className="absolute bottom-0 right-0 bg-primary text-on-primary p-1 rounded-full shadow-lg hover:bg-primary-container transition-colors disabled:opacity-50"
                >
                  {avatarUploading ? (
                    <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                  ) : (
                    <span className="material-symbols-outlined text-[16px]">edit</span>
                  )}
                </button>
              </div>
            </div>
            <div className="flex-1 w-full space-y-md">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-xs">{t('username')}</label>
                  <input
                    className="w-full bg-surface-bg border border-outline-variant rounded-lg px-md py-sm font-body-md text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    type="text"
                    readOnly
                    value={userInfo?.username || ''}
                  />
                </div>
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-xs">{t('email')}</label>
                  <input
                    className="w-full bg-surface-bg border border-outline-variant rounded-lg px-md py-sm font-body-md text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    type="email"
                    readOnly
                    value={userInfo?.email || ''}
                  />
                </div>
              </div>
              <div className="flex justify-start">
                <button className="flex items-center gap-xs font-label-md text-label-md text-primary hover:text-primary-container transition-colors">
                  <span className="material-symbols-outlined text-[18px]">lock_reset</span>
                  {t('changePassword')}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Bento Grid Layout for Settings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
          {/* Appearance Settings Card */}
          <div className="bg-card-bg rounded-xl p-lg shadow-soft border border-border hover:-translate-y-[2px] transition-transform duration-200">
            <div className="flex items-center gap-sm mb-md">
              <span className="material-symbols-outlined text-primary">palette</span>
              <h3 className="text-xl font-semibold text-on-surface">{t('appearance')}</h3>
            </div>
            <div className="space-y-md">
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-xs">{t('language')}</label>
                <FluidDropdown
                  value={locale}
                  onChange={(val) => setLocale(val as any)}
                  className="w-full"
                  options={[
                    { id: 'zh', label: '中文 (简体)', icon: Languages, color: '#FF6B6B' },
                    { id: 'en', label: 'English', icon: Globe, color: '#45B7D1' },
                  ]}
                />
              </div>
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-sm">{t('themeMode')}</label>
                <SlidingSwitch 
                  value={theme}
                  onChange={setTheme}
                  options={[
                    { label: t('light'), value: 'light', icon: 'light_mode' },
                    { label: t('dark'), value: 'dark', icon: 'dark_mode' },
                    { label: t('system'), value: 'system', icon: 'devices' },
                  ]}
                />
              </div>
            </div>
          </div>

          {/* Notification Preferences Card */}
          <div className="bg-card-bg rounded-xl p-lg shadow-soft border border-border hover:-translate-y-[2px] transition-transform duration-200">
            <div className="flex items-center gap-sm mb-md">
              <span className="material-symbols-outlined text-primary">notifications</span>
              <h3 className="text-xl font-semibold text-on-surface">{t('notifications')}</h3>
            </div>
            <div className="space-y-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-label-md text-label-md text-on-surface">{t('humanHandoffAlert')}</p>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">{t('humanHandoffDesc')}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input defaultChecked className="sr-only peer" type="checkbox" />
                  <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
              </div>
              <hr className="border-outline-variant" />
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-label-md text-label-md text-on-surface">{t('systemErrorAlert')}</p>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">{t('systemErrorDesc')}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input defaultChecked className="sr-only peer" type="checkbox" />
                  <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-surface-container-lowest after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface-container-lowest after:border-outline-variant after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Chat Widget Preview & Config Card */}
          <div className="bg-card-bg rounded-xl p-lg shadow-soft border border-border md:col-span-2 hover:-translate-y-[2px] transition-transform duration-200">
            <div className="flex items-center gap-sm mb-md">
              <span className="material-symbols-outlined text-primary">chat_bubble</span>
              <h3 className="text-xl font-semibold text-on-surface">{t('chatWidgetConfig')}</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-xs">{t('welcomeMessage')}</label>
                <textarea
                  className="w-full bg-surface-bg border border-outline-variant rounded-lg px-md py-sm font-body-md text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                  placeholder="Enter the greeting message..."
                  rows={4}
                  defaultValue="您好！欢迎使用 TianTing 客服系统。请问有什么我可以帮您的？"
                />
              </div>
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-xs">{t('maxHistory')}</label>
                <p className="font-body-sm text-body-sm text-on-surface-variant mb-sm">{t('maxHistoryDesc')}</p>
                <div className="relative w-32">
                  <input
                    className="w-full bg-surface-bg border border-outline-variant rounded-lg px-md py-sm font-code text-code text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-center"
                    max={50}
                    min={1}
                    type="number"
                    defaultValue={10}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* About Section Card */}
          <div className="bg-card-bg rounded-xl p-lg shadow-soft border border-border md:col-span-2 flex flex-col sm:flex-row items-center justify-between gap-md">
            <div className="flex items-center gap-md">
              <div className="w-12 h-12 rounded-lg overflow-hidden border border-primary/20">
                <img 
                  alt="Logo" 
                  className="w-full h-full object-cover" 
                  src={BrandLogo.src} 
                />
              </div>
              <div className="flex items-baseline gap-sm">
                <h4 className="font-h3 text-h3 text-on-surface">TianTing</h4>
                <span className="font-code text-code text-on-surface-variant">v1.0.0</span>
              </div>
            </div>
            <button onClick={handleCheckUpdate} className="px-md py-sm border border-outline-variant rounded-lg font-label-md text-label-md text-on-surface hover:bg-surface-bg transition-colors duration-200">
              {t('checkUpdates')}
            </button>
          </div>
        </div>
        </>
        )}
      </div>
      <AvatarCropper
        image={cropperImage || ''}
        visible={showCropper}
        onConfirm={handleCropConfirm}
        onCancel={handleCropCancel}
      />
    </div>
  );
}
