'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Input, DatePicker, Button, Table, Space, Typography, Drawer, Spin, Card } from 'antd';
import { SearchOutlined, UserOutlined, ClockCircleOutlined, MessageOutlined, EllipsisOutlined } from '@ant-design/icons';
import { useTranslations } from 'next-intl';
import { FluidDropdown } from '@/components/ui/fluid-dropdown';
import { Filter, Activity, CheckCircle2, Clock, ArrowRightLeft, MessageSquare, HelpCircle, History, Bot } from 'lucide-react';
import { historyApi } from '@/lib/api';

const { RangePicker } = DatePicker;
const { Text } = Typography;

const avatarGradients: Record<string, string> = {
  A: 'from-rose-400 to-pink-500',
  B: 'from-violet-400 to-purple-500',
  C: 'from-blue-400 to-indigo-500',
  D: 'from-cyan-400 to-teal-500',
  E: 'from-emerald-400 to-green-500',
  F: 'from-amber-400 to-orange-500',
  G: 'from-pink-400 to-rose-500',
  H: 'from-indigo-400 to-violet-500',
  I: 'from-teal-400 to-cyan-500',
  J: 'from-orange-400 to-amber-500',
  K: 'from-purple-400 to-fuchsia-500',
  L: 'from-sky-400 to-blue-500',
  M: 'from-green-400 to-emerald-500',
  N: 'from-fuchsia-400 to-pink-500',
  O: 'from-cyan-400 to-sky-500',
  P: 'from-red-400 to-rose-500',
  Q: 'from-blue-400 to-indigo-500',
  R: 'from-emerald-400 to-teal-500',
  S: 'from-amber-400 to-yellow-500',
  T: 'from-violet-400 to-purple-500',
  U: 'from-teal-400 to-emerald-500',
  V: 'from-pink-400 to-fuchsia-500',
  W: 'from-indigo-400 to-blue-500',
  X: 'from-orange-400 to-red-500',
  Y: 'from-green-400 to-lime-500',
  Z: 'from-purple-400 to-violet-500',
};

function getAvatarGradient(name: string): string {
  const initial = (name || 'A').charAt(0).toUpperCase();
  return avatarGradients[initial] || 'from-primary to-indigo-500';
}

function formatTime(isoString: string) {
  if (!isoString) return { date: '-', time: '-' };
  try {
    const d = new Date(isoString);
    const date = d.toISOString().slice(0, 10);
    const time = isoString.slice(11, 16);
    return { date, time };
  } catch {
    return { date: isoString, time: '' };
  }
}

function formatDuration(seconds: number | string) {
  const s = typeof seconds === 'string' ? parseInt(seconds, 10) : seconds;
  if (s == null || isNaN(s) || s < 0) return '-';
  const rounded = Math.round(s);
  if (rounded < 60) return `${rounded}秒`;
  const m = Math.floor(rounded / 60);
  const remainS = rounded % 60;
  return remainS > 0 ? `${m}分${remainS}秒` : `${m}分`;
}

export default function HistoryPage() {
  const t = useTranslations('History');
  const tc = useTranslations('Common');
  const [intent, setIntent] = useState('all');
  const [status, setStatus] = useState('all');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailsVisible, setDetailsVisible] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<any>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<any>(null);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  const fetchData = useCallback(async (params?: { search?: string; intent?: string; status?: string; startDate?: string; endDate?: string; page?: number; pageSize?: number }) => {
    setLoading(true);
    try {
      const queryParams: Record<string, unknown> = {};
      if (params?.search) queryParams.search = params.search;
      if (params?.intent && params.intent !== 'all') queryParams.intent = params.intent;
      if (params?.status && params.status !== 'all') queryParams.status = params.status;
      if (params?.startDate) queryParams.start_date = params.startDate;
      if (params?.endDate) queryParams.end_date = params.endDate;
      queryParams.page = params?.page || 1;
      queryParams.page_size = params?.pageSize || 10;

      const res: any = await historyApi.list(queryParams);
      const resData = res?.data || res;
      const items = Array.isArray(resData?.items) ? resData.items : [];
      setData(items);
      setPagination({
        current: resData?.page || 1,
        pageSize: resData?.page_size || 10,
        total: resData?.total || 0,
      });
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const columns = [
    {
      title: t('columns.user'),
      dataIndex: 'userName',
      key: 'user',
      render: (text: string) => (
        <Space size={10}>
          <div className={`w-9 h-9 rounded-full bg-gradient-to-br ${getAvatarGradient(text)} flex items-center justify-center text-white text-sm font-semibold ring-2 ring-white shadow-sm`}>
            {(text || 'U').charAt(0).toUpperCase()}
          </div>
          <Text strong className="text-on-surface text-[15px] font-semibold">{text}</Text>
        </Space>
      )
    },
    {
      title: t('columns.intent'),
      dataIndex: 'intent',
      key: 'intent',
      render: (intent: string) => {
        const styleMap: Record<string, { border: string; bg: string; text: string; dot: string }> = {
          'FAQ': { border: 'border-blue-300/60', bg: 'bg-blue-50/80', text: 'text-blue-700', dot: 'bg-blue-500' },
          'After-sales': { border: 'border-amber-300/60', bg: 'bg-amber-50/80', text: 'text-amber-700', dot: 'bg-amber-500' },
          'Chat': { border: 'border-emerald-300/60', bg: 'bg-emerald-50/80', text: 'text-emerald-700', dot: 'bg-emerald-500' },
        };
        const labelMap: Record<string, string> = {
          'FAQ': t('intents.faq'),
          'After-sales': t('intents.aftersale'),
          'Chat': t('intents.chat'),
        };
        const s = styleMap[intent] || { border: 'border-outline-variant', bg: 'bg-surface-container-low', text: 'text-on-surface-variant', dot: 'bg-on-surface-variant' };
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${s.border} ${s.bg} ${s.text}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
            {labelMap[intent] || intent}
          </span>
        );
      }
    },
    {
      title: t('columns.time'),
      dataIndex: 'startedAt',
      key: 'time',
      render: (text: string) => {
        const { date, time } = formatTime(text);
        return (
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold text-on-surface">{date}</span>
            <span className="text-xs text-on-surface-variant flex items-center gap-1">
              <ClockCircleOutlined className="text-[10px]" />
              {time}
            </span>
          </div>
        );
      }
    },
    {
      title: t('columns.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const isResolved = status === 'Resolved' || status === 'resolved';
        const isProcessing = status === 'Processing' || status === 'processing';
        const isTransferred = status === 'Transferred' || status === 'transferred';
        const isActive = status === 'active';

        let dotColor = 'bg-red-500';
        let bgClass = 'bg-red-50/80';
        let textClass = 'text-red-700';
        let borderClass = 'border-red-200/60';

        if (isResolved) { dotColor = 'bg-emerald-500'; bgClass = 'bg-emerald-50/80'; textClass = 'text-emerald-700'; borderClass = 'border-emerald-200/60'; }
        else if (isProcessing) { dotColor = 'bg-blue-500'; bgClass = 'bg-blue-50/80'; textClass = 'text-blue-700'; borderClass = 'border-blue-200/60'; }
        else if (isTransferred) { dotColor = 'bg-amber-500'; bgClass = 'bg-amber-50/80'; textClass = 'text-amber-700'; borderClass = 'border-amber-200/60'; }

        const labelMap: Record<string, string> = {
          'Resolved': t('statuses.resolved'),
          'Processing': t('statuses.processing'),
          'Transferred': t('statuses.transferred'),
        };
        return (
          <div className={`px-3 py-1 rounded-full inline-flex items-center gap-1.5 text-xs font-medium border ${borderClass} ${bgClass} ${textClass}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${dotColor} animate-pulse`} />
            {labelMap[status] || status}
          </div>
        );
      }
    },
    {
      title: t('columns.channel'),
      dataIndex: 'channel',
      key: 'channel',
      render: (channel: string) => {
        const isFeishu = channel === 'feishu';
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            isFeishu ? 'bg-blue-50/80 text-blue-700 border-blue-200/60' : 'bg-surface-container-low text-on-surface-variant border-outline-variant/60'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isFeishu ? 'bg-blue-500' : 'bg-on-surface-variant'}`} />
            <span className="material-symbols-outlined text-[14px]">
              {isFeishu ? 'mail' : 'language'}
            </span>
            {isFeishu ? '飞书' : 'Web'}
          </span>
        );
      }
    },
    {
      title: t('columns.messages'),
      dataIndex: 'messageCount',
      key: 'messages',
      align: 'center' as const,
      render: (count: number) => (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-surface-container-low text-on-surface-variant text-xs font-medium">
          <MessageOutlined className="text-[11px]" />
          {count}
        </span>
      )
    },
    {
      title: t('columns.duration'),
      dataIndex: 'duration',
      key: 'duration',
      render: (val: number | string) => (
        <span className="text-xs text-on-surface-variant flex items-center gap-1">
          <ClockCircleOutlined className="text-[10px]" />
          {formatDuration(val)}
        </span>
      )
    },
    {
      title: t('columns.preview'),
      dataIndex: 'preview',
      key: 'preview',
      ellipsis: true,
      render: (text: string) => (
        <div className="relative max-w-[200px]">
          <Text type="secondary" italic className="text-xs block truncate">"{text}"</Text>
          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-r from-transparent to-card-bg pointer-events-none" />
        </div>
      )
    },
    {
      title: t('columns.action'),
      key: 'action',
      render: (_: any, record: any) => (
        <Button
          type="default"
          size="small"
          icon={<EllipsisOutlined />}
          onClick={() => {
            setSelectedRecord(record);
            setDetailsVisible(true);
            setDetailsLoading(true);
            historyApi.get(record.id).then((res: any) => {
              setSelectedRecord(res?.data || res || record);
            }).catch(() => {
              setSelectedRecord(record);
            }).finally(() => {
              setDetailsLoading(false);
            });
          }}
          className="rounded-full border-outline-variant/60 hover:border-primary hover:text-primary transition-colors flex items-center"
        >
          {t('details')}
        </Button>
      )
    }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-card-bg rounded-xl shadow-soft overflow-hidden border border-outline-variant">
        <div className="relative p-6 pb-5 flex items-center justify-between border-b border-outline-variant bg-surface-container-low/30 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-primary/[0.02] to-transparent pointer-events-none" />
          <div className="relative flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <History size={22} strokeWidth={1.8} />
            </div>
            <div>
              <h2 className="text-[22px] font-semibold text-on-surface tracking-tight">{t('title')}</h2>
              <p className="text-sm text-on-surface-variant mt-1.5">{t('subtitle')}</p>
            </div>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
        </div>

        <div className="p-6">
          <div className="rounded-xl bg-surface-container-low/50 border border-outline-variant/60 p-4 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Filter size={14} className="text-on-surface-variant" />
              <span className="text-xs font-medium text-on-surface-variant uppercase tracking-wider">{t('search')}</span>
            </div>
            <div className="flex flex-wrap gap-3 items-center">
              <Input
                placeholder={t('searchPlaceholder')}
                prefix={<SearchOutlined className="text-on-surface-variant" />}
                size="large"
                className="w-full md:w-64 rounded-lg"
                allowClear
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
              <FluidDropdown
                value={intent}
                onChange={setIntent}
                className="w-40"
                options={[
                  { id: 'all', label: t('intent'), icon: Filter, color: '#94a3b8' },
                  { id: 'faq', label: t('intents.faq'), icon: HelpCircle, color: '#3b82f6' },
                  { id: 'aftersale', label: t('intents.aftersale'), icon: Activity, color: '#f59e0b' },
                  { id: 'chat', label: t('intents.chat'), icon: MessageSquare, color: '#10b981' },
                ]}
              />
              <FluidDropdown
                value={status}
                onChange={setStatus}
                className="w-40"
                options={[
                  { id: 'all', label: t('status'), icon: Activity, color: '#94a3b8' },
                  { id: 'resolved', label: t('statuses.resolved'), icon: CheckCircle2, color: '#10b981' },
                  { id: 'processing', label: t('statuses.processing'), icon: Clock, color: '#3b82f6' },
                  { id: 'transferred', label: t('statuses.transferred'), icon: ArrowRightLeft, color: '#f59e0b' },
                ]}
              />
              <RangePicker
                size="large"
                className="rounded-lg shadow-sm"
                value={dateRange as any}
                onChange={(dates) => setDateRange(dates as any)}
              />
              <Button
                type="primary"
                size="large"
                className="rounded-lg px-8 font-semibold shadow-md border-none bg-primary hover:bg-primary/90 transition-all active:scale-95"
                onClick={() => {
                  const params: { search: string; intent: string; status: string; startDate?: string; endDate?: string } = {
                    search: searchText,
                    intent,
                    status,
                  };
                  if (dateRange?.[0]) params.startDate = dateRange[0].format('YYYY-MM-DD');
                  if (dateRange?.[1]) params.endDate = dateRange[1].format('YYYY-MM-DD');
                  fetchData(params);
                }}
              >
                {t('search')}
              </Button>
            </div>
          </div>

          <Table
            columns={columns}
            dataSource={data}
            loading={loading}
            rowClassName={(_, index) => index % 2 === 1 ? 'bg-surface-container-low/30' : ''}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              className: "mt-4",
              onChange: (page, pageSize) => {
                const params: { search: string; intent: string; status: string; page: number; pageSize: number; startDate?: string; endDate?: string } = {
                  search: searchText,
                  intent,
                  status,
                  page,
                  pageSize,
                };
                if (dateRange?.[0]) params.startDate = dateRange[0].format('YYYY-MM-DD');
                if (dateRange?.[1]) params.endDate = dateRange[1].format('YYYY-MM-DD');
                fetchData(params);
              }
            }}
            className="border border-outline-variant rounded-lg overflow-hidden"
            size="middle"
          />

          <Drawer
            title={t('details')}
            placement="right"
            width={600}
            onClose={() => setDetailsVisible(false)}
            open={detailsVisible}
          >
            {detailsLoading ? (
              <div className="flex justify-center items-center h-full">
                <Spin size="large" />
              </div>
            ) : selectedRecord ? (
              <div className="space-y-6">
                <Card
                  size="small"
                  title={
                    <span className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
                        <UserOutlined className="text-primary text-xs" />
                      </div>
                      <span className="text-on-surface font-medium">基本信息</span>
                    </span>
                  }
                  className="shadow-soft border-outline-variant/60"
                >
                  <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                    {[
                      { label: t('columns.user'), value: selectedRecord.userName || selectedRecord.user || '-' },
                      { label: t('columns.intent'), value: selectedRecord.intent || '-' },
                      { label: t('columns.time'), value: selectedRecord.startedAt || selectedRecord.time || '-', isTime: true },
                      { label: t('columns.status'), value: selectedRecord.status || '-', isStatus: true },
                      { label: t('columns.channel'), value: selectedRecord.channel || '-' },
                      { label: t('columns.duration'), value: selectedRecord.duration || '-', isDuration: true },
                    ].map((item, idx) => (
                      <div key={idx} className={idx % 2 === 0 ? 'pr-4 border-r border-outline-variant/40' : ''}>
                        <div className="text-[11px] text-on-surface-variant font-medium uppercase tracking-wider mb-1">{item.label}</div>
                        {item.isTime ? (
                          (() => {
                            const { date, time } = formatTime(item.value);
                            return (
                              <div className="text-sm text-on-surface">
                                <div className="font-medium">{date}</div>
                                <div className="text-xs text-on-surface-variant">{time}</div>
                              </div>
                            );
                          })()
                        ) : item.isDuration ? (
                          <div className="text-sm text-on-surface">{formatDuration(selectedRecord.duration)}</div>
                        ) : item.isStatus ? (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-container text-on-surface border border-outline-variant/60">
                            {item.value}
                          </span>
                        ) : (
                          <div className="text-sm text-on-surface">{item.value}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>

                <Card
                  size="small"
                  title={
                    <span className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
                        <MessageOutlined className="text-primary text-xs" />
                      </div>
                      <span className="text-on-surface font-medium">历史记录</span>
                    </span>
                  }
                  className="shadow-soft border-outline-variant/60"
                >
                  <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                    {selectedRecord.messages && selectedRecord.messages.length > 0 ? (
                      selectedRecord.messages.map((msg: any, i: number) => {
                        const isUser = msg.role === 'user';
                        return (
                          <div key={i} className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                            <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-semibold shadow-sm ${
                              isUser
                                ? `bg-gradient-to-br ${getAvatarGradient(selectedRecord.userName || selectedRecord.user || 'U')} text-white`
                                : 'bg-primary-container text-primary'
                            }`}>
                              {isUser
                                ? (selectedRecord.userName || selectedRecord.user || 'U').charAt(0).toUpperCase()
                                : <Bot size={16} />
                              }
                            </div>
                            <div className={`max-w-[75%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                              <div className={`px-3.5 py-2.5 shadow-sm ${
                                isUser
                                  ? 'bg-primary/10 text-on-surface rounded-2xl rounded-tr-md'
                                  : 'bg-surface-container text-on-surface rounded-2xl rounded-tl-md'
                              }`}>
                                <span className="text-sm leading-relaxed">{msg.content}</span>
                              </div>
                              {msg.timestamp && (
                                <span className="text-[10px] text-on-surface-variant/70 mt-1 px-1">
                                  {(() => {
                                    const { date, time } = formatTime(msg.timestamp);
                                    return `${date} ${time}`;
                                  })()}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center text-on-surface-variant py-8">暂无详细记录</div>
                    )}
                  </div>
                </Card>
              </div>
            ) : null}
          </Drawer>
      </div>
      </div>
    </div>
  );
}