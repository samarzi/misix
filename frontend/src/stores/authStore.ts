/**
 * Auth Store - Telegram-only authentication
 * 
 * This store manages authentication state for Telegram WebApp users.
 * The application uses Telegram-based authentication via the Telegram bot.
 */

import { create } from 'zustand';

interface User {
  id: string;
  telegram_id: number;
  full_name?: string;
  username?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start with loading state
  error: null,

  setUser: (user: User | null) => {
    set({
      user,
      isAuthenticated: !!user,
      isLoading: false,
    });
  },

  setLoading: (isLoading: boolean) => {
    set({ isLoading });
  },

  setError: (error: string | null) => {
    set({ error, isLoading: false });
  },

  clearError: () => {
    set({ error: null });
  },

  logout: () => {
    localStorage.removeItem('misix_user_id');
    set({
      user: null,
      isAuthenticated: false,
      error: null,
    });
  },
}));
