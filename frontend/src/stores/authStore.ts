import { create } from 'zustand';
import axios from 'axios';
import { API_BASE_URL } from '../config';

interface User {
  id: string;
  email: string;
  full_name?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  clearError: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v2/auth/login`, {
        email,
        password,
      });

      const { tokens, user } = response.data;
      
      // Store tokens
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      
      set({
        user,
        token: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Ошибка входа';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw new Error(errorMessage);
    }
  },

  register: async (email: string, password: string, fullName?: string) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v2/auth/register`, {
        email,
        password,
        full_name: fullName,
      });

      const { tokens, user } = response.data;
      
      // Store tokens
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      
      set({
        user,
        token: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Ошибка регистрации';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw new Error(errorMessage);
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      error: null,
    });
  },

  refreshAccessToken: async () => {
    const { refreshToken } = get();
    
    if (!refreshToken) {
      get().logout();
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v2/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { tokens } = response.data;
      
      localStorage.setItem('access_token', tokens.access_token);
      if (tokens.refresh_token) {
        localStorage.setItem('refresh_token', tokens.refresh_token);
      }
      
      set({
        token: tokens.access_token,
        refreshToken: tokens.refresh_token || refreshToken,
      });
    } catch (error) {
      console.error('Token refresh failed:', error);
      get().logout();
      throw error;
    }
  },

  clearError: () => {
    set({ error: null });
  },

  checkAuth: () => {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (token && refreshToken) {
      set({
        token,
        refreshToken,
        isAuthenticated: true,
      });
    } else {
      set({
        token: null,
        refreshToken: null,
        isAuthenticated: false,
      });
    }
  },
}));

// Configure axios interceptors
axios.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await useAuthStore.getState().refreshAccessToken();
        
        // Retry original request with new token
        const token = useAuthStore.getState().token;
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
