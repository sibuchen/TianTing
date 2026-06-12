'use client';

import React, { useEffect, useState } from 'react';
import { ConfigProvider, theme as antdTheme, App } from 'antd';
import { useSettingStore } from '@/store/settingStore';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import { NextIntlClientProvider } from 'next-intl';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';

// Import messages
import zhMessages from '@/messages/zh.json';
import enMessages from '@/messages/en.json';

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme, locale } = useSettingStore();
  const [mounted, setMounted] = useState(false);

  // Determine actual theme if system
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    setMounted(true);
    let actualTheme: 'light' | 'dark';

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const systemIsDark = mediaQuery.matches;
      setIsDarkMode(systemIsDark);
      actualTheme = systemIsDark ? 'dark' : 'light';
      
      const listener = (e: MediaQueryListEvent) => {
        setIsDarkMode(e.matches);
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      };
      mediaQuery.addEventListener('change', listener);
      document.documentElement.setAttribute('data-theme', actualTheme);
      return () => mediaQuery.removeEventListener('change', listener);
    } else {
      setIsDarkMode(theme === 'dark');
      actualTheme = theme === 'dark' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', actualTheme);
    }
  }, [theme]);

  const antdLocale = locale === 'zh' ? zhCN : enUS;
  const messages = locale === 'zh' ? zhMessages : enMessages;

  return (
    <AntdRegistry>
      <NextIntlClientProvider locale={locale} messages={messages} timeZone="Asia/Shanghai">
        {mounted ? (
          <ConfigProvider
            locale={antdLocale}
            theme={{
              algorithm: isDarkMode ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
              token: {
                colorPrimary: isDarkMode ? '#afc6ff' : '#0057c2',
                borderRadius: 8,
                fontFamily: 'Inter, PingFang SC, Microsoft YaHei, sans-serif',
              },
            }}
          >
            <App>
              {children}
            </App>
          </ConfigProvider>
        ) : (
          <div style={{ visibility: 'hidden' }}>{children}</div>
        )}
      </NextIntlClientProvider>
    </AntdRegistry>
  );
}
