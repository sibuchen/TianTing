'use client';
 
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { SlidingSwitch } from '@/components/ui/SlidingSwitch';
import { dashboardApi } from '@/lib/api';

interface DashboardMetrics {
  todayConversations: number;
  todayConversationsTrend: number;
  resolutionRate: number;
  resolutionRateTrend: number;
  avgResponseTime: number;
  avgResponseTimeTrend: number;
}

interface RealtimeStatus {
  autoServing: number;
  humanServing: number;
  waiting: number;
}

interface IntentItem {
  name: string;
  percentage: number;
  color: string;
}

interface RecentConversation {
  id: string;
  userName: string;
  userAvatar: string | null;
  intent: string;
  time: string;
  status: string;
}

interface ChannelDistributionItem {
  channel: string;
  count: number;
  percentage: number;
}

const defaultMetrics: DashboardMetrics = {
  todayConversations: 0,
  todayConversationsTrend: 0,
  resolutionRate: 0,
  resolutionRateTrend: 0,
  avgResponseTime: 0,
  avgResponseTimeTrend: 0,
};

const defaultRealtime: RealtimeStatus = {
  autoServing: 0,
  humanServing: 0,
  waiting: 0,
};

export default function DashboardPage() {
  const t = useTranslations('Dashboard');
  const t_history = useTranslations('History');
  const [range, setRange] = React.useState('today');
  const [metrics, setMetrics] = useState<DashboardMetrics>(defaultMetrics);
  const [realtime, setRealtime] = useState<RealtimeStatus>(defaultRealtime);
  const [intents, setIntents] = useState<IntentItem[]>([]);
  const [conversations, setConversations] = useState<RecentConversation[]>([]);
  const [channelDist, setChannelDist] = useState<ChannelDistributionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [metricsRes, realtimeRes, intentRes, convRes, channelRes]: any[] = await Promise.allSettled([
          dashboardApi.getMetrics(),
          dashboardApi.getRealtimeStatus(),
          dashboardApi.getIntentDistribution(),
          dashboardApi.getRecentConversations(),
          dashboardApi.getChannelDistribution(),
        ]).then(results => results.map(r => r.status === 'fulfilled' ? r.value : null));

        if (metricsRes) setMetrics(metricsRes);
        if (realtimeRes) setRealtime(realtimeRes);
        if (intentRes) setIntents(intentRes);
        if (convRes) setConversations(convRes);
        if (channelRes) setChannelDist(channelRes);
      } catch {
        // use default data
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [range]);

  const statusIcon = (status: string) => {
    if (status === 'auto_resolved') return <span className="material-symbols-outlined text-[16px]">robot_2</span>;
    if (status === 'human_agent') return <span className="material-symbols-outlined text-[16px]">person</span>;
    return <span className="material-symbols-outlined text-[16px]">schedule</span>;
  };

  const statusColor = (status: string) => {
    if (status === 'auto_resolved') return 'text-success';
    if (status === 'human_agent') return 'text-secondary';
    return 'text-warning';
  };

  const statusLabel = (status: string) => {
    if (status === 'auto_resolved') return t('recentConversations.autoResolved');
    if (status === 'human_agent') return t('recentConversations.humanAgent');
    return t('recentConversations.waiting');
  };

  const intentColorMap: Record<string, string> = {
    'bg-primary': 'bg-primary',
    'bg-info': 'bg-info',
    'bg-warning': 'bg-warning',
    'bg-outline-variant': 'bg-outline-variant',
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="space-y-8">
        {/* Page Header & Filter */}
        <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-on-surface">{t('title')}</h1>
          <p className="text-sm text-on-surface-variant mt-1">{t('subtitle')}</p>
        </div>
        <SlidingSwitch 
          value={range}
          onChange={setRange}
          className="min-w-[240px]"
          options={[
            { label: t('today'), value: 'today' },
            { label: t('week'), value: 'week' },
            { label: t('month'), value: 'month' },
          ]}
        />
      </div>

      {/* Metric Cards (Top Section) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1 */}
        <div className="bg-card-bg rounded-[12px] p-4 shadow-soft hover:-translate-y-[2px] hover:shadow-lg transition-all relative overflow-hidden border border-outline-variant">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center gap-2 text-on-surface-variant">
              <span className="material-symbols-outlined text-[20px]">chat</span>
              <span className="text-sm font-medium">{t('metrics.todayConversations')}</span>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-success/10 text-success flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">trending_up</span> {metrics.todayConversationsTrend}%
            </span>
          </div>
          <div className="text-3xl font-semibold text-on-surface">{metrics.todayConversations}</div>
        </div>
        
        {/* Card 2 */}
        <div className="bg-card-bg rounded-[12px] p-4 shadow-soft hover:-translate-y-[2px] hover:shadow-lg transition-all relative overflow-hidden border border-outline-variant">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center gap-2 text-on-surface-variant">
              <span className="material-symbols-outlined text-[20px]">check_circle</span>
              <span className="text-sm font-medium">{t('metrics.resolutionRate')}</span>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-success/10 text-success flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">trending_up</span> {metrics.resolutionRateTrend}%
            </span>
          </div>
          <div className="text-3xl font-semibold text-on-surface">{metrics.resolutionRate}%</div>
        </div>

        {/* Card 3 */}
        <div className="bg-card-bg rounded-[12px] p-4 shadow-soft hover:-translate-y-[2px] hover:shadow-lg transition-all relative overflow-hidden border border-outline-variant">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center gap-2 text-on-surface-variant">
              <span className="material-symbols-outlined text-[20px]">timer</span>
              <span className="text-sm font-medium">{t('metrics.avgResponseTime')}</span>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-success/10 text-success flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">trending_down</span> {metrics.avgResponseTimeTrend}s
            </span>
          </div>
          <div className="text-3xl font-semibold text-on-surface">{metrics.avgResponseTime}s</div>
        </div>
      </div>

      {/* Middle Section: Real-time & Intent */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Real-time Status */}
        <div className="bg-card-bg rounded-[12px] p-4 shadow-soft border border-outline-variant flex flex-col">
          <h3 className="text-xl font-semibold text-on-surface mb-6 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span>
            {t('realtimeStatus.title')}
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-surface-container-low border border-outline-variant relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent"></div>
              <span className="material-symbols-outlined text-[20px] text-primary mb-1 relative z-10">smart_toy</span>
              <span className="text-xs font-medium text-on-surface-variant mb-1 uppercase tracking-wider relative z-10">{t('realtimeStatus.auto')}</span>
              <span className="text-2xl font-semibold text-primary relative z-10">{realtime.autoServing}</span>
            </div>
            <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-surface-container-low border border-outline-variant relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-secondary/5 to-transparent"></div>
              <span className="material-symbols-outlined text-[20px] text-secondary mb-1 relative z-10">person</span>
              <span className="text-xs font-medium text-on-surface-variant mb-1 uppercase tracking-wider relative z-10">{t('realtimeStatus.human')}</span>
              <span className="text-2xl font-semibold text-secondary relative z-10">{realtime.humanServing}</span>
            </div>
            <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-error-container/30 border border-error/20 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-error/5 to-transparent"></div>
              <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-error animate-ping"></div>
              <span className="material-symbols-outlined text-[20px] text-error mb-1 relative z-10">schedule</span>
              <span className="text-xs font-medium text-on-error-container mb-1 uppercase tracking-wider relative z-10">{t('realtimeStatus.waiting')}</span>
              <span className="text-2xl font-semibold text-error relative z-10">{realtime.waiting}</span>
            </div>
          </div>
          <div className="border-t border-outline-variant my-4"></div>
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant">swap_horiz</span>
              <span className="text-xs font-medium text-on-surface-variant uppercase tracking-wider">{t('realtimeStatus.channels')}</span>
            </div>
            <div className="space-y-3">
              {channelDist.length > 0 ? channelDist.map((item) => {
                const isFeishu = item.channel === 'feishu';
                const brandColor = isFeishu ? '#3b82f6' : '#64748b';
                const iconName = isFeishu ? 'mail' : 'language';
                const channelName = isFeishu ? '飞书' : 'Web';
                return (
                  <div key={item.channel} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-container-low transition-colors group">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0" style={{ backgroundColor: `${brandColor}15` }}>
                      <span className="material-symbols-outlined text-[16px]" style={{ color: brandColor }}>{iconName}</span>
                    </div>
                    <span className="text-sm font-medium text-on-surface min-w-[40px]">{channelName}</span>
                    <div className="flex-1 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${item.percentage}%`, backgroundColor: brandColor }}></div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant group-hover:bg-surface-container-highest transition-colors">{item.count}</span>
                  </div>
                );
              }) : (
                <>
                  <div className="flex items-center gap-3 px-3 py-2 rounded-lg">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 bg-[#64748b15]">
                      <span className="material-symbols-outlined text-[16px] text-[#64748b]">language</span>
                    </div>
                    <span className="text-sm font-medium text-on-surface min-w-[40px]">Web</span>
                    <div className="flex-1 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-outline-variant/50" style={{ width: '50%' }}></div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant">--</span>
                  </div>
                  <div className="flex items-center gap-3 px-3 py-2 rounded-lg">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 bg-[#3b82f615]">
                      <span className="material-symbols-outlined text-[16px] text-[#3b82f6]">mail</span>
                    </div>
                    <span className="text-sm font-medium text-on-surface min-w-[40px]">飞书</span>
                    <div className="flex-1 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-outline-variant/50" style={{ width: '50%' }}></div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant">--</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Intent Distribution */}
        <div className="bg-card-bg rounded-[12px] p-4 shadow-soft border border-outline-variant">
          <h3 className="text-xl font-semibold text-on-surface mb-6">{t('intentDistribution.title')}</h3>
          <div className="space-y-4">
            {intents.length > 0 ? intents.map((item, idx) => {
              const colorClass = ['bg-primary', 'bg-info', 'bg-warning', 'bg-outline-variant'][idx % 4] || 'bg-outline-variant';
              return (
                <div key={idx}>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-on-surface">{item.name}</span>
                    <span className="text-on-surface-variant">{item.percentage}%</span>
                  </div>
                  <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <div className={`h-full ${intentColorMap[item.color] || colorClass} rounded-full`} style={{ width: `${item.percentage}%` }}></div>
                  </div>
                </div>
              );
            }) : (
              <>
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-on-surface">{t('intentDistribution.productInquiry')}</span>
                    <span className="text-on-surface-variant">45%</span>
                  </div>
                  <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: '45%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-on-surface">{t('intentDistribution.orderStatus')}</span>
                    <span className="text-on-surface-variant">30%</span>
                  </div>
                  <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <div className="h-full bg-info rounded-full" style={{ width: '30%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-on-surface">{t('intentDistribution.returnsRefunds')}</span>
                    <span className="text-on-surface-variant">15%</span>
                  </div>
                  <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <div className="h-full bg-warning rounded-full" style={{ width: '15%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-on-surface">{t('intentDistribution.other')}</span>
                    <span className="text-on-surface-variant">10%</span>
                  </div>
                  <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <div className="h-full bg-outline-variant rounded-full" style={{ width: '10%' }}></div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Section: Recent Conversations */}
      <div className="bg-card-bg rounded-[12px] shadow-soft border border-outline-variant overflow-hidden">
        <div className="p-4 border-b border-outline-variant flex justify-between items-center">
          <h3 className="text-xl font-semibold text-on-surface">{t('recentConversations.title')}</h3>
          <Link href="/history" className="text-sm font-medium text-primary hover:text-primary-container transition-colors">
            {t('recentConversations.viewAll')}
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low text-xs font-medium text-on-surface-variant">
                <th className="p-4 font-medium border-b border-outline-variant">{t_history('columns.user')}</th>
                <th className="p-4 font-medium border-b border-outline-variant">{t_history('columns.intent')}</th>
                <th className="p-4 font-medium border-b border-outline-variant">{t_history('columns.time')}</th>
                <th className="p-4 font-medium border-b border-outline-variant">{t_history('columns.status')}</th>
                <th className="p-4 font-medium border-b border-outline-variant text-right">{t_history('columns.action')}</th>
              </tr>
            </thead>
            <tbody className="text-sm text-on-surface divide-y divide-outline-variant">
              {conversations.length > 0 ? conversations.map((conv) => (
                <tr key={conv.id} className="hover:bg-surface-container-lowest transition-colors group">
                  <td className="p-4 flex items-center gap-3">
                    {conv.userAvatar ? (
                      <img alt={conv.userName} className="w-8 h-8 rounded-full" src={conv.userAvatar} />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-warning/20 text-warning flex items-center justify-center font-bold">{conv.userName?.[0] || '?'}</div>
                    )}
                    <span className="font-medium">{conv.userName}</span>
                  </td>
                  <td className="p-4"><span className="px-2 py-1 rounded-md bg-surface-variant text-on-surface-variant text-xs font-medium text-[11px]">{conv.intent}</span></td>
                  <td className="p-4 text-on-surface-variant">{conv.time}</td>
                  <td className="p-4">
                    <span className={`flex items-center gap-1 ${statusColor(conv.status)}`}>
                      {statusIcon(conv.status)} {statusLabel(conv.status)}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <Link href="/history" className="text-xs font-medium text-primary hover:underline opacity-0 group-hover:opacity-100 transition-opacity">{t('recentConversations.viewDetails')}</Link>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td className="p-8 text-center text-on-surface-variant" colSpan={5}>{loading ? '...' : t('recentConversations.noData') || 'No data'}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      </div>
    </div>
  );
}
