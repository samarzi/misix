export const resolveUserId = () => {
  const telegramUserId = (window as any)?.Telegram?.WebApp?.initDataUnsafe?.user?.id;
  if (telegramUserId) {
    return String(telegramUserId);
  }

  const fromQuery = new URLSearchParams(window.location.search).get('user_id');
  if (fromQuery) {
    return fromQuery;
  }

  const fallback = import.meta.env.VITE_DEMO_USER_ID ?? 'demo-user';
  return fallback;
};
