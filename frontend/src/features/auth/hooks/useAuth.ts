/**
 * useAuth Hook - Telegram-based authentication
 * 
 * This hook manages authentication state for Telegram WebApp users.
 * It fetches user data from the backend using the Telegram ID.
 */

import { useEffect } from 'react';
import { useAuthStore } from '../../../stores/authStore';
import { getUserByTelegramId } from '../../../api/client';

export const useAuth = () => {
  const { user, isAuthenticated, isLoading, setUser, setLoading, setError } = useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);

        // Get Telegram user ID from WebApp
        const telegramWebApp = (window as any)?.Telegram?.WebApp;
        const telegramUser = telegramWebApp?.initDataUnsafe?.user;

        if (!telegramUser?.id) {
          console.warn('No Telegram user found - running in demo mode');
          // In demo mode, try to use stored user_id or fallback
          const storedUserId = localStorage.getItem('misix_user_id');
          if (storedUserId) {
            setUser({
              id: storedUserId,
              telegram_id: 0,
              full_name: 'Demo User',
              username: 'demo',
            });
          } else {
            setUser(null);
          }
          return;
        }

        // Fetch user data from backend using Telegram ID
        const userData = await getUserByTelegramId(telegramUser.id);
        
        // Store user_id in localStorage for resolveUserId()
        localStorage.setItem('misix_user_id', userData.id);
        
        setUser({
          id: userData.id,
          telegram_id: userData.telegram_id,
          full_name: userData.full_name,
          username: userData.username,
        });
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        setError('Failed to authenticate');
        setUser(null);
      }
    };

    initAuth();
  }, [setUser, setLoading, setError]);

  return {
    user,
    isAuthenticated,
    isLoading,
  };
};
