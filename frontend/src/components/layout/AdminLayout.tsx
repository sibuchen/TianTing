'use client';

import React from 'react';
import { Layout, Menu, Button, Dropdown, Space, Avatar, Badge, Breadcrumb } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  RobotOutlined,
  ToolOutlined,
  BookOutlined,
  CustomerServiceOutlined,
  HistoryOutlined,
  TeamOutlined,
  KeyOutlined,
  SettingOutlined,
  BellOutlined,
  GlobalOutlined,
  UserOutlined,
  LogoutOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { usePathname, useRouter } from 'next/navigation';
import { useSettingStore } from '@/store/settingStore';
import { useAuthStore } from '@/store/authStore';
import { Moon, Sun } from 'lucide-react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { humanServiceApi } from '@/lib/api';
import { FluidDropdown } from '@/components/ui/fluid-dropdown';
import { User, LogOut } from 'lucide-react';
import { LanguageToggle } from '@/components/ui/language-toggle';


const { Header, Sider, Content } = Layout;

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { theme, setTheme, locale, setLocale, sidebarCollapsed, toggleSidebar } = useSettingStore();
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations('Common');

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const toggleLanguage = () => {
    setLocale(locale === 'zh' ? 'en' : 'zh');
  };

  const { user } = useAuthStore();
  const isAdmin = user?.role === 'admin';
  const isOperator = user?.role === 'operator';

  const [pendingCount, setPendingCount] = React.useState(0);

  React.useEffect(() => {
    if (!isOperator) return;

    const fetchPendingCount = async () => {
      try {
        const res: any = await humanServiceApi.getQueue();
        const data = Array.isArray(res?.data) ? res.data : [];
        setPendingCount(data.filter((u: any) => u.status === 'waiting').length);
      } catch {
        // silently fail
      }
    };

    fetchPendingCount();
    const timer = setInterval(fetchPendingCount, 15000);
    return () => clearInterval(timer);
  }, [isOperator]);

  const adminMenuItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: t('dashboard') },
    { key: '/agents', icon: <RobotOutlined />, label: t('agents') },
    { key: '/skills', icon: <ThunderboltOutlined />, label: t('skills') },
    { key: '/tools', icon: <ToolOutlined />, label: t('tools') },
    { key: '/knowledge', icon: <BookOutlined />, label: t('knowledge') },
    { key: '/history', icon: <HistoryOutlined />, label: t('history') },
    { key: '/users', icon: <TeamOutlined />, label: t('users') },
    { key: '/api-keys', icon: <KeyOutlined />, label: t('apiKeys') },
    { key: '/settings', icon: <SettingOutlined />, label: t('settings') },
  ];

  const operatorMenuItems = [
    { key: '/human-service', icon: <CustomerServiceOutlined />, label: t('humanService') },
    { key: '/history', icon: <HistoryOutlined />, label: t('history') },
    { key: '/settings', icon: <SettingOutlined />, label: t('settings') },
  ];

  const menuItems = isAdmin ? adminMenuItems : operatorMenuItems;

  const activeIndex = menuItems.findIndex(item => item.key === pathname);
  const [sliderStyle, setSliderStyle] = React.useState({ top: 0, height: 48, opacity: 0 });

  React.useEffect(() => {
    // Small delay to ensure Ant Design has finished updating the DOM classes
    const timer = setTimeout(() => {
      const activeItem = document.querySelector('.admin-sidebar-menu .ant-menu-item-selected') as HTMLElement;
      const menu = document.querySelector('.admin-sidebar-menu') as HTMLElement;

      if (activeItem && menu) {
        setSliderStyle({
          top: activeItem.offsetTop + menu.offsetTop,
          height: activeItem.offsetHeight,
          opacity: 1
        });
      } else {
        setSliderStyle(prev => ({ ...prev, opacity: 0 }));
      }
    }, 50);
    return () => clearTimeout(timer);
  }, [pathname, sidebarCollapsed]);

  // Helper to generate basic breadcrumb based on path
  const breadcrumbs = pathname.split('/').filter(p => p).map((p, index, arr) => {
    const url = `/${arr.slice(0, index + 1).join('/')}`;
    const menuItem = menuItems.find(item => item.key === url);
    return {
      title: menuItem ? menuItem.label : p.charAt(0).toUpperCase() + p.slice(1),
    };
  });

  return (
    <Layout className="min-h-screen bg-surface-bg transition-colors duration-300">
      <Sider
        trigger={null}
        collapsible
        collapsed={sidebarCollapsed}
        width={260}
        className="bg-card-bg relative z-10"
        style={{ background: 'var(--card-bg)' }}
      >
        <div className="flex items-end justify-center h-16 pb-2">
          <a
            href="https://github.com/sibuchen"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xl font-bold text-primary truncate px-4 hover:opacity-80 transition-opacity"
          >
            {sidebarCollapsed ? 'TiTi' : 'TianTing'}
          </a>
        </div>
        <div
          className="sidebar-sliding-bg"
          style={{
            top: sliderStyle.top,
            height: sliderStyle.height,
            opacity: sliderStyle.opacity,
            visibility: sliderStyle.opacity ? 'visible' : 'hidden'
          }}
        />
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          onClick={({ key }) => router.push(key)}
          style={{
            borderRight: 0,
            marginTop: 0,
            paddingTop: 0,
            background: 'transparent'
          }}
          className="admin-sidebar-menu"
        />
      </Sider>

      <Layout style={{ background: 'transparent' }}>
        <Header className="bg-transparent flex items-center justify-between h-16 p-0 leading-[64px] transition-colors duration-300">
          <div className="flex items-center">
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleSidebar}
              style={{ fontSize: '16px', width: 64, height: 64 }}
            />
            <Breadcrumb items={breadcrumbs} className="ml-4" />
          </div>

          <div className="flex items-center pr-6 gap-4">
            {isOperator && (
              <Badge count={pendingCount} size="small">
                <Button
                  type="text"
                  icon={<BellOutlined />}
                  onClick={() => router.push('/human-service')}
                />
              </Badge>
            )}

            <LanguageToggle locale={locale} onToggle={toggleLanguage} />


            <Button type="text" onClick={toggleTheme} icon={theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />} />

            <FluidDropdown
              options={[
                { id: 'profile', label: t('profile'), icon: User },
                { id: 'logout', label: t('logout'), icon: LogOut, color: '#ff4d4f' },
              ]}
              onOptionClick={(opt) => {
                if (opt.id === 'logout') router.push('/login');
              }}
            >
              <div className="flex items-center cursor-pointer ml-2">
                <Avatar src={user?.avatar || undefined} icon={<UserOutlined />} className="bg-primary" />
              </div>
            </FluidDropdown>
          </div>
        </Header>

        <Content className="bg-transparent flex-1 transition-all duration-300 overflow-y-auto">
          <div className="h-full w-full">
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
