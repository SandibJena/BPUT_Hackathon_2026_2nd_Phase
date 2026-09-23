import axios from 'axios';
import { Token, User, TextIntakeRequest, TriageNote } from './types';
import { getToken, clearToken } from './auth';

const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL,
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearToken();
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  auth: {
    login: async (username: string, password: string):Promise<Token> => {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      const res = await apiClient.post<Token>('/auth/token', formData);
      return res.data;
    },
    me: async ():Promise<User> => {
      const res = await apiClient.get<User>('/auth/me');
      return res.data;
    }
  },
  intake: {
    submitText: async (data: TextIntakeRequest):Promise<TriageNote> => {
      const res = await apiClient.post<TriageNote>('/intake/text', data);
      return res.data;
    }
  },
  notes: {
    list: async (filters?: Record<string, string>):Promise<TriageNote[]> => {
      const res = await apiClient.get<TriageNote[]>('/notes', { params: filters });
      return res.data;
    },
    get: async (id: string):Promise<TriageNote> => {
      const res = await apiClient.get<TriageNote>(`/notes/${id}`);
      return res.data;
    },
    updateReview: async (id: string, data: any):Promise<TriageNote> => {
      const res = await apiClient.put<TriageNote>(`/notes/${id}/review`, data);
      return res.data;
    }
  }
};
