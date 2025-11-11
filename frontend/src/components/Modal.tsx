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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-6">
      <div className="w-full max-w-lg rounded-lg border border-border bg-surface p-6 shadow-card">
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-text">{title}</h2>
          <Button variant="ghost" onClick={onClose} aria-label="Закрыть модалку">
            ✖️
          </Button>
        </div>
        <div className="mt-4 flex flex-col gap-4 text-sm text-text">{children}</div>
        <div className="mt-6 flex justify-end gap-3">
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
