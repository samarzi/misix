interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

const EmptyState = ({ title, description, action }: EmptyStateProps) => {
  return (
    <div className="group relative flex flex-col items-center justify-center gap-4 overflow-hidden rounded-2xl border border-dashed border-borderStrong bg-surfaceAlt/60 px-6 py-10 text-center text-textSecondary shadow-card backdrop-blur-xl">
      <span className="pointer-events-none absolute inset-0 border border-transparent transition-colors duration-500 ease-out-soft group-hover:border-primaryGlow" aria-hidden="true" />
      <h3 className="text-xl font-semibold text-text">{title}</h3>
      <p className="max-w-md text-sm text-textMuted">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
};

export default EmptyState;
