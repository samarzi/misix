import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  onBack?: () => void;
}

const SectionHeader = ({ title, subtitle, actions, onBack }: SectionHeaderProps) => {
  return (
    <div className="relative flex flex-col gap-4 overflow-hidden rounded-2xl border border-borderStrong bg-surface/70 p-5 shadow-card backdrop-blur-xl transition-transform duration-350 ease-out-soft hover:-translate-y-0.5 hover:shadow-glow md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-4">
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            className="rounded-full border border-borderStrong bg-surfaceGlass px-4 py-1.5 text-sm font-medium text-textSecondary transition-colors hover:border-primary hover:text-text"
          >
            ← Назад
          </button>
        )}
        <div>
          <h2 className="text-xl font-semibold text-text">{title}</h2>
          {subtitle && <p className="text-sm text-textMuted">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </div>
  );
};

export default SectionHeader;
