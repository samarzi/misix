import type { PropsWithChildren, ReactNode } from 'react';

interface AppLayoutProps extends PropsWithChildren {
  header?: ReactNode;
  footer?: ReactNode;
}

const AppLayout = ({ header, footer, children }: AppLayoutProps) => {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-text">
      <div className="pointer-events-none absolute inset-0 bg-radial-overlay opacity-70" aria-hidden="true" />
      <div className="pointer-events-none absolute -top-40 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-primaryGlow blur-3xl" aria-hidden="true" />
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 px-4 pb-12 pt-[calc(env(safe-area-inset-top)+theme(spacing.8))] md:px-8 lg:px-10">
        {header && <header className="flex flex-col gap-4">{header}</header>}
        <main className="flex-1">{children}</main>
        {footer && <footer className="rounded-2xl border border-borderStrong bg-surface/70 px-6 py-4 text-center text-sm text-textSecondary backdrop-blur-xl">{footer}</footer>}
      </div>
    </div>
  );
};

export default AppLayout;
