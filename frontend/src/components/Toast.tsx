import { useEffect, useMemo } from 'react';
import clsx from 'clsx';
import { useUiStore } from '../stores/uiStore';

const toastColors: Record<'success' | 'error' | 'info', string> = {
  success: 'border-success/40 bg-success/15 text-success',
  error: 'border-danger/40 bg-danger/15 text-danger',
  info: 'border-primary/40 bg-primaryMuted/40 text-primary',
};

const Toast = () => {
  const hideToast = useUiStore((state) => state.hideToast);
  const toast = useUiStore((state) => state.toast);
  const toastVisible = toast.visible;
  const toastContent = useMemo(
    () => ({
      message: toast.message,
      type: toast.type,
    }),
    [toast.message, toast.type],
  );

  useEffect(() => {
    if (!toastVisible) return undefined;
    const timer = window.setTimeout(() => hideToast(), 4000);
    return () => window.clearTimeout(timer);
  }, [toastVisible, hideToast]);

  if (!toastVisible) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed inset-x-0 top-6 z-[1000] flex justify-center px-4 md:justify-end md:pr-8">
      <div
        className={clsx(
          'pointer-events-auto flex min-w-[260px] max-w-sm items-start gap-3 rounded-2xl border px-4 py-3 shadow-glow backdrop-blur-xl transition-transform duration-300 ease-out-soft',
          toastColors[toastContent.type],
        )}
      >
        <span className="text-xl">
          {toastContent.type === 'success' && '✅'}
          {toastContent.type === 'error' && '⚠️'}
          {toastContent.type === 'info' && 'ℹ️'}
        </span>
        <div className="flex-1 text-sm font-medium leading-snug text-text">
          <p>{toastContent.message}</p>
        </div>
        <button
          type="button"
          className="rounded-full border border-borderStrong bg-surfaceGlass px-2 py-1 text-xs font-semibold text-text hover:bg-surface/80"
          onClick={hideToast}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default Toast;
