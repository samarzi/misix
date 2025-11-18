/**
 * Auth Store - Simplified for Telegram-only authentication
 * 
 * Note: This store has been simplified to remove email/password authentication.
 * The application uses Telegram-based authentication via the Telegram bot.
 * 
 * If you need to add authentication state management for Telegram users in the future,
 * you can implement it here.
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
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  setUser: (user: User | null) => {
    set({
      user,
      isAuthenticated: !!user,
    });
  },

  clearError: () => {
    set({ error: null });
  },
}));
