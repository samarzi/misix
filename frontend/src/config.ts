const DEFAULT_API_URL = 'https://misix.onrender.com';
const DEFAULT_TONE = 'teasing';

const TELEGRAM_START_PARAM_KEY = 'backend';
const LOCAL_PORT = '5173';

const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '::1']);

const decodeParam = (value?: string | null) => {
  if (!value) return null;
  try {
    const normalized = decodeURIComponent(value);
    if (/^https?:\/\//i.test(normalized)) {
      return normalized.replace(/\/$/, '');
    }
  } catch (error) {
    console.warn('Failed to decode backend param', error);
  }
  return null;
};

const getBackendFromQuery = () => {
  const params = new URLSearchParams(window.location.search);
  return decodeParam(params.get('backend'));
};

const getBackendFromHash = () => {
  if (!window.location.hash) return null;
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
  return decodeParam(params.get('backend'));
};

const getBackendFromTelegram = () => {
  const raw = (window as any)?.Telegram?.WebApp?.initDataUnsafe?.start_param;
  if (!raw) return null;
  const params = new URLSearchParams(raw.replace(/;/g, '&'));
  return decodeParam(params.get(TELEGRAM_START_PARAM_KEY) ?? raw);
};

const getBackendFromEnv = () => {
  const env = import.meta.env.VITE_API_BASE_URL as string | undefined;
  return decodeParam(env ?? undefined);
};

const resolveBackendBaseUrl = () => {
  const fromEnv = getBackendFromEnv();
  if (fromEnv) return fromEnv;

  const fromQuery = getBackendFromQuery();
  if (fromQuery) return fromQuery;

  const fromHash = getBackendFromHash();
  if (fromHash) return fromHash;

  const fromTelegram = getBackendFromTelegram();
  if (fromTelegram) return fromTelegram;

  const isLocal = LOCAL_HOSTS.has(window.location.hostname) && window.location.port === LOCAL_PORT;
  if (isLocal) {
    return 'http://localhost:8000';
  }

  return DEFAULT_API_URL;
};

export const API_BASE_URL = resolveBackendBaseUrl();
export const TONE_STORAGE_KEY = 'misix_tone_style';
export const DEFAULT_TONE_STYLE = DEFAULT_TONE;
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const TELEGRAM_AVAILABLE = Boolean((window as any)?.Telegram?.WebApp);

export const MISIX_TONE_STYLES = [
  { key: 'neutral', label: 'Нейтральный' },
  { key: 'teasing', label: 'Подшучивающий' },
  { key: 'business', label: 'Деловой' },
] as const;

export type ToneStyle = typeof MISIX_TONE_STYLES[number]['key'];
