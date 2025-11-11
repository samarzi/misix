import { create } from 'zustand';
import { DEFAULT_TONE_STYLE, MISIX_TONE_STYLES, TONE_STORAGE_KEY } from '../config';

export type DashboardView = 'summary' | 'detail';
export type DashboardSectionKey = 'analytics' | 'tasks' | 'notes' | 'finances' | 'debts' | 'reminders' | 'personal';

export type FinanceTabKey = 'overview' | 'accounts' | 'categories' | 'rules';

export type ModalType =
  | null
  | 'task'
  | 'task-delete'
  | 'finance-transaction'
  | 'finance-delete-transaction'
  | 'finance-account'
  | 'finance-category'
  | 'finance-rule'
  | 'finance-delete-account'
  | 'finance-delete-category'
  | 'finance-delete-rule'
  | 'note'
  | 'note-delete'
  | 'reminder'
  | 'reminder-cancel'
  | 'personal-category'
  | 'personal-delete-category'
  | 'personal-entry'
  | 'personal-delete-entry'
  | 'pin';

export interface ModalPayload {
  entityId?: string;
  mode?: 'create' | 'edit' | 'delete';
  context?: Record<string, unknown>;
}

export interface ModalState {
  type: ModalType;
  payload?: ModalPayload;
}

export interface PinState {
  enabled: boolean;
  locked: boolean;
  error?: string | null;
}

export type ToastType = 'success' | 'error' | 'info';

export interface ToastState {
  visible: boolean;
  message: string;
  type: ToastType;
}

export interface UiState {
  view: DashboardView;
  section: DashboardSectionKey;
  financeTab: FinanceTabKey;
  tone: string;
  modal: ModalState;
  pin: PinState;
  toast: ToastState;
  setView: (view: DashboardView) => void;
  setSection: (section: DashboardSectionKey) => void;
  setFinanceTab: (tab: FinanceTabKey) => void;
  setTone: (tone: string) => void;
  openModal: (type: ModalType, payload?: ModalPayload) => void;
  closeModal: () => void;
  setPinState: (pin: Partial<PinState>) => void;
  showToast: (message: string, type?: ToastType) => void;
  hideToast: () => void;
}

const resolveInitialTone = () => {
  const stored = window.localStorage.getItem(TONE_STORAGE_KEY);
  if (stored && MISIX_TONE_STYLES.some((tone) => tone.key === stored)) {
    return stored;
  }
  return DEFAULT_TONE_STYLE;
};

export const useUiStore = create<UiState>((set) => ({
  view: 'summary',
  section: 'analytics',
  financeTab: 'overview',
  tone: resolveInitialTone(),
  modal: { type: null },
  pin: {
    enabled: false,
    locked: false,
    error: null,
  },
  toast: {
    visible: false,
    message: '',
    type: 'info',
  },
  setView: (view) => set({ view }),
  setSection: (section) => set({ section, view: 'detail' }),
  setFinanceTab: (financeTab) => set({ financeTab }),
  setTone: (tone) => {
    window.localStorage.setItem(TONE_STORAGE_KEY, tone);
    set({ tone });
  },
  openModal: (type, payload) => set({ modal: { type, payload } }),
  closeModal: () => set({ modal: { type: null } }),
  setPinState: (pin) =>
    set((state) => ({
      pin: {
        ...state.pin,
        ...pin,
      },
    })),
  showToast: (message, type = 'info') =>
    set({
      toast: {
        visible: true,
        message,
        type,
      },
    }),
  hideToast: () =>
    set({
      toast: {
        visible: false,
        message: '',
        type: 'info',
      },
    }),
}));
