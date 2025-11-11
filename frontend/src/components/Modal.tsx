import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import Button from './Button';

interface ModalProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

const modalRoot = typeof document !== 'undefined' ? document.body : null;

const Modal = ({ title, onClose, children, actions }: ModalProps) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  if (!modalRoot) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 px-4 py-10 backdrop-blur-xl">
      <div className="w-full max-w-xl animate-float-slow rounded-3xl border border-borderStrong bg-surface/80 p-8 shadow-glow backdrop-blur-2xl">
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textMuted">Диалог</p>
            <h2 className="text-2xl font-semibold text-text">{title}</h2>
          </div>
          <Button variant="ghost" onClick={onClose} aria-label="Закрыть модалку" className="text-xl">
            ✕
          </Button>
        </div>
        <div className="mt-6 flex flex-col gap-5 text-sm text-textSecondary">{children}</div>
        <div className="mt-8 flex justify-end gap-3">
          {actions ?? (
            <Button variant="secondary" onClick={onClose}>
              Закрыть
            </Button>
          )}
        </div>
      </div>
    </div>,
    modalRoot,
  );
};

export default Modal;
