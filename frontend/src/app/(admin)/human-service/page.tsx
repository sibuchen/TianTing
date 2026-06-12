'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { humanServiceApi } from '@/lib/api';

interface ChatMessage {
  id: string;
  role: string;
  content: string;
  timestamp: string | null;
}

interface LastMessage {
  content: string;
  role: string;
  timestamp: string | null;
}

interface QueuedUser {
  conversationId: string;
  userId: string | null;
  userName: string | null;
  userAvatar: string | null;
  intent: string | null;
  channel: string;
  waitingDuration: number;
  status: string;
  lastMessage: LastMessage | null;
}

function formatWaitTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  return `${hours}h ${mins % 60}m`;
}

function formatTime(isoString: string | null): string {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getIntentIcon(intent: string | null): string {
  switch (intent) {
    case 'After-sales': return 'sell';
    case 'Order Status': return 'shopping_cart';
    case 'Product Query': return 'help';
    default: return 'autorenew';
  }
}

function getAvatarColor(index: number): string {
  const colors = ['bg-primary', 'bg-secondary', 'bg-tertiary', 'bg-info'];
  return colors[index % colors.length];
}

export default function HumanServicePage() {
  const t = useTranslations('HumanService');
  const router = useRouter();

  const [queueUsers, setQueueUsers] = useState<QueuedUser[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [activeConversationId, setActiveConversationId] = useState('');
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelayRef = useRef(1000);
  const urlRestoredRef = useRef(false);

  const fetchQueue = useCallback(async () => {
    try {
      const res: any = await humanServiceApi.getQueue();
      const data = Array.isArray(res?.data) ? res.data : [];
      setQueueUsers(data);
    } catch {
      // silently fail, keep existing data
    }
  }, []);

  const fetchMessages = useCallback(async (conversationId: string) => {
    setMessagesLoading(true);
    setError('');
    try {
      const res: any = await humanServiceApi.getConversationMessages(conversationId);
      const msgs = res?.data?.messages ?? [];
      setMessages(msgs);
    } catch {
      setError('加载消息失败');
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  const handleSelectUser = useCallback(async (user: QueuedUser) => {
    setActiveConversationId(user.conversationId);
    setError('');

    router.replace(`/human-service?conversationId=${user.conversationId}`);

    if (user.status === 'waiting') {
      try {
        await humanServiceApi.acceptConversation(user.conversationId);
        setQueueUsers(prev =>
          prev.map(u =>
            u.conversationId === user.conversationId
              ? { ...u, status: 'active' }
              : u
          )
        );
      } catch {
        // may already be accepted
      }
    }

    await fetchMessages(user.conversationId);
  }, [fetchMessages, router]);

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || !activeConversationId) return;

    const content = inputValue.trim();
    setInputValue('');
    setSending(true);

    try {
      const res: any = await humanServiceApi.sendMessage(activeConversationId, { content });
      const newMsg: ChatMessage = {
        id: res?.data?.id ?? Date.now().toString(),
        role: 'human_agent',
        content: content,
        timestamp: res?.data?.timestamp ?? new Date().toISOString(),
      };
      setMessages(prev => [...prev, newMsg]);
    } catch {
      setError('发送消息失败');
    } finally {
      setSending(false);
    }
  }, [inputValue, activeConversationId]);

  const handleEndService = useCallback(async () => {
    if (!activeConversationId) return;
    try {
      await humanServiceApi.endConversation(activeConversationId);
      setQueueUsers(prev =>
        prev.filter(u => u.conversationId !== activeConversationId)
      );
      setActiveConversationId('');
      setMessages([]);
      router.replace('/human-service');
    } catch {
      setError('结束服务失败');
    }
  }, [activeConversationId, router]);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/admin`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      reconnectDelayRef.current = 1000;
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'new_conversation' || msg.type === 'conversation_update') {
          fetchQueue();
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
      const delay = reconnectDelayRef.current;
      reconnectDelayRef.current = Math.min(delay * 2, 30000);
      reconnectTimerRef.current = setTimeout(() => {
        connectWebSocket();
      }, delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [fetchQueue]);

  useEffect(() => {
    fetchQueue().finally(() => setLoading(false));
  }, [fetchQueue]);

  useEffect(() => {
    if (urlRestoredRef.current || loading) return;
    const params = new URLSearchParams(window.location.search);
    const convId = params.get('conversationId');
    if (!convId) return;

    const user = queueUsers.find(u => u.conversationId === convId);
    if (user) {
      urlRestoredRef.current = true;
      handleSelectUser(user);
    }
  }, [queueUsers, loading, handleSelectUser]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  const activeUser = queueUsers.find(u => u.conversationId === activeConversationId);

  return (
    <div className="max-w-[1600px] mx-auto p-6 h-[calc(100vh-64px)] flex flex-col">
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="material-symbols-outlined animate-spin text-primary text-3xl">progress_activity</span>
        </div>
      ) : (
      <div className="flex-1 flex overflow-hidden bg-surface-container-low rounded-xl border border-outline-variant shadow-sm">
      {/* Left Sidebar: Queue */}
      <aside className="w-80 bg-surface-container-low flex flex-col h-full z-10">
        <div className="p-md bg-surface-container-high flex justify-between items-center">
          <h2 className="font-h3 text-h3 text-on-surface">{t('queue')}</h2>
          <div className="flex items-center gap-2">
            <span className="font-label-sm text-label-sm text-on-surface-variant bg-surface-variant px-2 py-1 rounded-full">
              {queueUsers.length} {t('waiting')}
            </span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-sm gap-sm flex flex-col scrollbar-thin">
          {queueUsers.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-on-surface-variant gap-2">
              <span className="material-symbols-outlined text-4xl">inbox</span>
              <p className="font-body-sm text-body-sm">{t('noWaitingUsers') || '暂无等待中的用户'}</p>
            </div>
          ) : (
            queueUsers.map((user, index) => (
              <div
                key={user.conversationId}
                onClick={() => handleSelectUser(user)}
                className={`rounded-lg p-md cursor-pointer transition-all ${
                  activeConversationId === user.conversationId
                    ? 'bg-primary-container border-l-4 border-primary shadow-soft'
                    : 'bg-card-bg border border-outline-variant hover:shadow-soft'
                }`}
              >
                <div className="flex items-start gap-2 mb-2">
                  <div className={`w-10 h-10 rounded-full ${getAvatarColor(index)} flex items-center justify-center text-on-primary-fixed font-label-lg text-label-lg uppercase shrink-0`}>
                    {user.userName?.charAt(0) || '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <span className="font-label-md text-label-md text-on-surface font-semibold truncate">
                        {user.userName || '未知用户'}
                      </span>
                      <span className={`font-label-sm text-label-sm shrink-0 ml-2 ${
                        user.waitingDuration > 60 ? 'text-error' : 'text-warning'
                      }`}>
                        {formatWaitTime(user.waitingDuration)}
                      </span>
                    </div>
                    <div className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1 mt-0.5">
                      <span className="material-symbols-outlined text-[14px]">
                        {getIntentIcon(user.intent)}
                      </span>
                      {user.intent || t('intents.general') || '通用咨询'}
                    </div>
                  </div>
                </div>
                {user.lastMessage && (
                  <div className="mt-2 px-2 py-1.5 bg-surface-container-low rounded text-xs text-on-surface-variant truncate">
                    <span className="font-medium">
                      {user.lastMessage.role === 'user' ? '用户' : user.lastMessage.role === 'agent' ? 'Agent' : '系统'}:
                    </span>{' '}
                    {user.lastMessage.content}
                  </div>
                )}
                {user.channel === 'feishu' && (
                  <div className="mt-1.5 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium w-fit">
                    <span className="material-symbols-outlined text-[12px]">mail</span>
                    飞书
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Right Area: Chat */}
      <section className="flex-1 flex flex-col h-full bg-surface relative">
        {!activeUser ? (
          <div className="flex-1 flex flex-col items-center justify-center text-on-surface-variant gap-3">
            <span className="material-symbols-outlined text-6xl">chat</span>
            <p className="font-body-lg text-body-lg">{t('selectUserHint') || '选择一个用户开始服务'}</p>
            <p className="font-body-sm text-body-sm">{t('selectUserHintDesc') || '点击左侧队列中的用户查看对话详情'}</p>
          </div>
        ) : (
          <>
            {/* Chat Header */}
            <div className="p-lg bg-card-bg flex justify-between items-center z-10">
              <div className="flex items-center gap-md">
                <div className={`w-12 h-12 rounded-full ${getAvatarColor(queueUsers.findIndex(u => u.conversationId === activeConversationId))} flex items-center justify-center text-on-primary-fixed font-h3 text-h3 uppercase`}>
                  {activeUser.userName?.charAt(0) || '?'}
                </div>
                <div>
                  <h2 className="font-h2 text-h2 text-on-surface flex items-center gap-2">
                    {activeUser.userName || '未知用户'}
                    {activeUser.channel === 'feishu' && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                        <span className="material-symbols-outlined text-[12px]">mail</span>
                        飞书
                      </span>
                    )}
                  </h2>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-1 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-primary">
                      {getIntentIcon(activeUser.intent)}
                    </span>
                    {activeUser.intent || '通用咨询'}
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                      activeUser.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {activeUser.status === 'active' ? (t('active') || '服务中') : (t('waiting') || '等待中')}
                    </span>
                  </p>
                </div>
              </div>
              <div className="flex gap-sm">
                <button
                  className="px-4 py-2 border border-error text-error rounded-lg font-label-md text-label-md hover:bg-error-container transition-all flex items-center gap-2 shadow-sm"
                  onClick={handleEndService}
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                  {t('endService')}
                </button>
              </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-lg flex flex-col gap-md bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjIiIGZpbGw9IiNlMGUyZWQiIGZpbGwtb3BhY2l0eT0iMC40Ii8+PC9zdmc+')] scrollbar-thin">
              {messagesLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <span className="material-symbols-outlined animate-spin text-primary text-2xl">progress_activity</span>
                </div>
              ) : messages.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-on-surface-variant">
                  <p className="font-body-sm">{t('noMessages') || '暂无消息记录'}</p>
                </div>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  const isAgent = msg.role === 'agent';
                  const isHumanAgent = msg.role === 'human_agent';
                  const isSystem = msg.role === 'system';
                  const isOutgoing = isHumanAgent;

                  if (isSystem) {
                    return (
                      <div key={msg.id} className="flex justify-center my-2">
                        <span className="font-label-sm text-label-sm text-on-surface-variant bg-surface-container-high px-3 py-1 rounded-full">
                          {msg.content}
                        </span>
                      </div>
                    );
                  }

                  return (
                    <div key={msg.id} className={`flex flex-col gap-xs max-w-[80%] ${isOutgoing ? 'self-end items-end' : 'self-start'}`}>
                      <span className={`font-label-sm text-label-sm text-on-surface-variant ${isOutgoing ? 'mr-2' : 'ml-2'}`}>
                        {isUser ? (activeUser.userName || '用户') : isAgent ? 'AI Assistant' : 'You'} · {formatTime(msg.timestamp)}
                      </span>
                      <div className={`p-md rounded-2xl shadow-sm font-body-md ${
                        isUser ? 'bg-primary text-on-primary rounded-tr-sm' :
                        isAgent ? 'bg-card-bg border border-outline-variant text-on-surface rounded-tl-sm' :
                        'bg-surface-container-high border border-outline-variant text-on-surface rounded-tl-sm'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  );
                })
              )}
              {error && (
                <div className="flex justify-center">
                  <span className="font-label-sm text-label-sm text-error bg-error-container px-3 py-1 rounded-full">{error}</span>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="p-md bg-card-bg z-10">
              <div className="relative">
                <textarea
                  className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-md pr-16 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary resize-none h-24 scrollbar-thin"
                  placeholder={t('typeMessage', { name: activeUser.userName || '' }) || `向 ${activeUser.userName || '用户'} 发送消息...`}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                ></textarea>
                <button
                  className="absolute right-3 bottom-3 w-10 h-10 bg-primary text-on-primary rounded-lg flex items-center justify-center hover:scale-[1.05] hover:bg-primary-container transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={handleSendMessage}
                  disabled={sending || !inputValue.trim()}
                >
                  <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>send</span>
                </button>
              </div>
            </div>
          </>
        )}
      </section>
      </div>
      )}
    </div>
  );
}