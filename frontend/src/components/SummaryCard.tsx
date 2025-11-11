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
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surfaceAlt p-4 shadow-card">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primaryMuted text-xl">
          {icon}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-base font-semibold text-text">{title}</h3>
            {action}
          </div>
          <p className="text-lg font-semibold text-text">{primary}</p>
          <p className="text-sm text-textMuted">{secondary}</p>
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;
