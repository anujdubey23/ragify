import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds for LLM generation
});

export const api = {
  // Health & Stats
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },
  getStats: async () => {
    const res = await apiClient.get('/api/stats');
    return res.data;
  },

  // Settings
  getSettings: async () => {
    const res = await apiClient.get('/api/settings');
    return res.data;
  },
  updateSettings: async (settings) => {
    const res = await apiClient.post('/api/settings', settings);
    return res.data;
  },

  // Document Management
  uploadDocument: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return res.data;
  },
  getDocuments: async () => {
    const res = await apiClient.get('/api/documents');
    return res.data;
  },
  getDocument: async (id) => {
    const res = await apiClient.get(`/api/documents/${id}`);
    return res.data;
  },
  deleteDocument: async (id) => {
    const res = await apiClient.delete(`/api/documents/${id}`);
    return res.data;
  },

  // Chat & Retrieval
  sendChatMessage: async (payload) => {
    const res = await apiClient.post('/api/chat', payload);
    return res.data;
  },
  getConversations: async () => {
    const res = await apiClient.get('/api/chats');
    return res.data;
  },
  getConversation: async (id) => {
    const res = await apiClient.get(`/api/chats/${id}`);
    return res.data;
  },
  deleteConversation: async (id) => {
    const res = await apiClient.delete(`/api/chats/${id}`);
    return res.data;
  },

  // Evaluation
  runEvaluation: async (customQuestions) => {
    const payload = customQuestions ? { questions: customQuestions } : {};
    const res = await apiClient.post('/api/evaluate', payload);
    return res.data;
  },
  getEvaluationHistory: async () => {
    const res = await apiClient.get('/api/evaluate/history');
    return res.data;
  },
  getEvaluationDataset: async () => {
    const res = await apiClient.get('/api/evaluate/dataset');
    return res.data;
  },
};

export default api;
