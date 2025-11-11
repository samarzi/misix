const UUID_PATTERN = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

const isValidUuid = (value?: string | null): value is string => Boolean(value && UUID_PATTERN.test(value));

const FALLBACK_DEMO_USER_ID = '00000000-0000-0000-0000-000000000000';

export const resolveUserId = () => {
  const telegramUserId = (window as any)?.Telegram?.WebApp?.initDataUnsafe?.user?.id;
  if (isValidUuid(telegramUserId)) {
    return String(telegramUserId);
  }

  const fromQuery = new URLSearchParams(window.location.search).get('user_id');
  if (isValidUuid(fromQuery)) {
    return fromQuery;
  }

  if (isValidUuid(import.meta.env.VITE_DEMO_USER_ID)) {
    return import.meta.env.VITE_DEMO_USER_ID;
  }

  return FALLBACK_DEMO_USER_ID;
};
