import type { ReactNode } from 'react';

interface SummaryCardProps {
  icon: ReactNode;
  title: string;
  primary: string;
  secondary: string;
  action?: ReactNode;
}

const SummaryCard = ({ icon, title, primary, secondary, action }: SummaryCardProps) => {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-borderStrong bg-surfaceAlt/70 p-5 shadow-card backdrop-blur-xl transition-transform duration-350 ease-out-soft hover:-translate-y-1 hover:shadow-glow">
      <span className="pointer-events-none absolute inset-0 border border-transparent transition-all duration-500 ease-out-soft group-hover:border-primaryGlow" aria-hidden="true" />
      <div className="relative flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primaryMuted text-2xl text-primary">
          {icon}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-base font-semibold text-text md:text-lg">{title}</h3>
            {action}
          </div>
          <p className="mt-1 text-2xl font-semibold text-text md:text-3xl">{primary}</p>
          <p className="text-sm text-textMuted">{secondary}</p>
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;
