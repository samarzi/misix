const UUID_PATTERN = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

const isValidUuid = (value?: string | null): value is string => Boolean(value && UUID_PATTERN.test(value));

const FALLBACK_DEMO_USER_ID = '00000000-0000-0000-0000-000000000000';

/**
 * Resolve user ID from various sources
 * Priority: URL query param > localStorage > demo user
 * 
 * Note: Telegram ID is handled separately by useAuth hook
 */
export const resolveUserId = () => {
  // Check URL query parameter first
  const fromQuery = new URLSearchParams(window.location.search).get('user_id');
  if (isValidUuid(fromQuery)) {
    return fromQuery;
  }

  // Check localStorage (set by useAuth hook)
  const fromStorage = localStorage.getItem('misix_user_id');
  if (isValidUuid(fromStorage)) {
    return fromStorage;
  }

  // Check environment variable for demo mode
  if (isValidUuid(import.meta.env.VITE_DEMO_USER_ID)) {
    return import.meta.env.VITE_DEMO_USER_ID;
  }

  return FALLBACK_DEMO_USER_ID;
};
