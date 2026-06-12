import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (data: { username: string; password: string; remember?: boolean }) =>
    api.post('/auth/login', data),

  register: (data: { username: string; email: string; password: string; phone: string; captchaId: string; captchaCode: string }) =>
    api.post('/auth/register', data),

  getCaptcha: () =>
    api.get('/auth/captcha'),

  refresh: (data: { refreshToken: string }) =>
    api.post('/auth/refresh', data),

  logout: () =>
    api.post('/auth/logout'),

  me: () =>
    api.get('/auth/me'),
};

export const dashboardApi = {
  getMetrics: () =>
    api.get('/dashboard/metrics'),

  getRealtimeStatus: () =>
    api.get('/dashboard/realtime-status'),

  getIntentDistribution: () =>
    api.get('/dashboard/intent-distribution'),

  getRecentConversations: () =>
    api.get('/dashboard/recent-conversations'),

  getChannelDistribution: () =>
    api.get('/dashboard/channel-distribution'),
};

export const agentsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/agents', { params }),

  get: (id: string) =>
    api.get(`/agents/${id}`),

  create: (data: Record<string, unknown>) =>
    api.post('/agents', data),

  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/agents/${id}`, data),

  delete: (id: string) =>
    api.delete(`/agents/${id}`),

  toggle: (id: string, isEnabled: boolean) =>
    api.patch(`/agents/${id}/toggle`, { is_enabled: isEnabled }),

  assignSkill: (agentId: string, skillId: string) =>
    api.post(`/agents/${agentId}/skills/${skillId}`),

  removeSkill: (agentId: string, skillId: string) =>
    api.delete(`/agents/${agentId}/skills/${skillId}`),

  linkMCPServer: (agentId: string, mcpServerId: string, isLinked: boolean) =>
    api.post(`/agents/${agentId}/mcp-servers`, { mcp_server_id: mcpServerId, is_linked: isLinked }),

  unlinkMCPServer: (agentId: string, mcpServerId: string) =>
    api.delete(`/agents/${agentId}/mcp-servers/${mcpServerId}`),

  toggleTool: (agentId: string, toolId: string, isEnabled: boolean) =>
    api.patch(`/agents/${agentId}/tools/${toolId}`, { is_enabled: isEnabled }),

  addSubAgent: (agentId: string, subAgentId: string) =>
    api.post(`/agents/${agentId}/sub-agents/${subAgentId}`),

  removeSubAgent: (agentId: string, subAgentId: string) =>
    api.delete(`/agents/${agentId}/sub-agents/${subAgentId}`),

  addKnowledgeDocument: (agentId: string, documentId: string) =>
    api.post(`/agents/${agentId}/knowledge-documents/${documentId}`),

  removeKnowledgeDocument: (agentId: string, documentId: string) =>
    api.delete(`/agents/${agentId}/knowledge-documents/${documentId}`),

  addKnowledgeQA: (agentId: string, qaId: string) =>
    api.post(`/agents/${agentId}/knowledge-qa/${qaId}`),

  removeKnowledgeQA: (agentId: string, qaId: string) =>
    api.delete(`/agents/${agentId}/knowledge-qa/${qaId}`),
};

export const toolsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/tools', { params }),

  get: (id: string) =>
    api.get(`/tools/${id}`),

  create: (data: Record<string, unknown>) =>
    api.post('/tools', data),

  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/tools/${id}`, data),

  delete: (id: string) =>
    api.delete(`/tools/${id}`),

  test: (id: string, data: Record<string, unknown>) =>
    api.post(`/tools/${id}/test`, data),

  listBuiltin: () =>
    api.get('/tools/built-in'),

  toggleBuiltinTool: (id: string, isEnabled: boolean) =>
    api.patch(`/tools/built-in/${id}`, { is_enabled: isEnabled }),

  getMcpTools: () =>
    api.get('/tools/mcp'),

  toggleMcpTool: (id: string, isEnabled: boolean) =>
    api.patch(`/tools/mcp/${id}`, { is_enabled: isEnabled }),

  bulkToggleMcpTool: (serverId: string, isEnabled: boolean) =>
    api.patch('/tools/mcp/bulk-toggle', { server_id: serverId, is_enabled: isEnabled }),
};

export const skillsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/skills', { params }),

  get: (id: string) =>
    api.get(`/skills/${id}`),

  create: (data: Record<string, unknown>) =>
    api.post('/skills', data),

  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/skills/${id}`, data),

  delete: (id: string) =>
    api.delete(`/skills/${id}`),

  getTags: () =>
    api.get('/skills/tags'),

  import: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/skills/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  export: (id: string) =>
    api.get(`/skills/${id}/export`, { responseType: 'blob' }),
};

export const knowledgeApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/knowledge', { params }),

  get: (id: string) =>
    api.get(`/knowledge/${id}`),

  create: (data: Record<string, unknown>) =>
    api.post('/knowledge', data),

  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/knowledge/${id}`, data),

  delete: (id: string) =>
    api.delete(`/knowledge/${id}`),

  listDocuments: (params?: Record<string, unknown>) =>
    api.get('/knowledge/documents', { params }),

  uploadDocument: (formData: FormData) =>
    api.post('/knowledge/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  deleteDocument: (documentId: string) =>
    api.delete(`/knowledge/documents/${documentId}`),

  retryDocument: (documentId: string) =>
    api.post(`/knowledge/documents/${documentId}/retry`),

  previewDocument: (documentId: string) =>
    api.get(`/knowledge/documents/${documentId}/preview`),

  listQA: (params?: Record<string, unknown>) =>
    api.get('/knowledge/qa', { params }),

  createQA: (data: { question: string; answer: string }) =>
    api.post('/knowledge/qa', data),

  updateQA: (qaId: string, data: { question: string; answer: string }) =>
    api.put(`/knowledge/qa/${qaId}`, data),

  deleteQA: (qaId: string) =>
    api.delete(`/knowledge/qa/${qaId}`),
};

export const humanServiceApi = {
  getQueue: () =>
    api.get('/human-service/queue'),

  getSessions: (params?: Record<string, unknown>) =>
    api.get('/human-service/sessions', { params }),

  getSession: (id: string) =>
    api.get(`/human-service/sessions/${id}`),

  assignSession: (id: string, data: Record<string, unknown>) =>
    api.post(`/human-service/sessions/${id}/assign`, data),

  closeSession: (id: string) =>
    api.post(`/human-service/sessions/${id}/close`),

  acceptConversation: (conversationId: string) =>
    api.post(`/human-service/conversations/${conversationId}/accept`),

  getConversationMessages: (conversationId: string, params?: Record<string, unknown>) =>
    api.get(`/human-service/conversations/${conversationId}/messages`, { params }),

  sendMessage: (conversationId: string, data: { content: string }) =>
    api.post(`/human-service/conversations/${conversationId}/messages`, data),

  endConversation: (conversationId: string) =>
    api.post(`/human-service/conversations/${conversationId}/end`),
};

export const historyApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/history', { params }),

  get: (id: string) =>
    api.get(`/history/${id}`),
};

export const usersApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/users', { params }),

  get: (id: string) =>
    api.get(`/users/${id}`),

  create: (data: Record<string, unknown>) =>
    api.post('/users', data),

  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/users/${id}`, data),

  delete: (id: string) =>
    api.delete(`/users/${id}`),
};

export const apiKeysApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/api-keys', { params }),

  get: (id: string) =>
    api.get(`/api-keys/${id}`),

  create: (data: Record<string, unknown>) =>
    api.post('/api-keys', data),

  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/api-keys/${id}`, data),

  delete: (id: string) =>
    api.delete(`/api-keys/${id}`),

  test: (id: string) =>
    api.post(`/api-keys/${id}/test`),
};

export const settingsApi = {
  get: () =>
    api.get('/settings'),

  update: (data: Record<string, unknown>) =>
    api.put('/settings', data),

  checkUpdate: () =>
    api.post('/settings/check-update'),

  uploadAvatar: (formData: FormData) =>
    api.post('/settings/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  changePassword: (data: { current_password: string; new_password: string; confirm_password: string }) =>
    api.put('/settings/password', data),

  getModelConfigs: () =>
    api.get('/settings/model-configs'),

  createModelConfig: (data: Record<string, unknown>) =>
    api.post('/settings/model-configs', data),

  updateModelConfig: (id: string, data: Record<string, unknown>) =>
    api.put(`/settings/model-configs/${id}`, data),

  deleteModelConfig: (id: string) =>
    api.delete(`/settings/model-configs/${id}`),

  testModelConfig: (id: string) =>
    api.post(`/settings/model-configs/${id}/test`),

  getMCPServers: () =>
    api.get('/settings/mcp-servers'),

  createMCPServer: (data: Record<string, unknown>) =>
    api.post('/settings/mcp-servers', data),

  updateMCPServer: (id: string, data: Record<string, unknown>) =>
    api.put(`/settings/mcp-servers/${id}`, data),

  deleteMCPServer: (id: string) =>
    api.delete(`/settings/mcp-servers/${id}`),

  testMCPServer: (id: string) =>
    api.post(`/settings/mcp-servers/${id}/test`),

  toggleMCPServer: (id: string, isEnabled: boolean) =>
    api.patch(`/settings/mcp-servers/${id}/toggle`, { is_enabled: isEnabled }),
};

export default api;
