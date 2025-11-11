import type { PropsWithChildren, ReactNode } from 'react';

interface AppLayoutProps extends PropsWithChildren {
  header?: ReactNode;
  footer?: ReactNode;
}

const AppLayout = ({ header, footer, children }: AppLayoutProps) => {
  return (
    <div className="min-h-screen bg-background text-text">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 px-4 py-6 md:px-6">
        {header && <header className="flex flex-col gap-4">{header}</header>}
        <main className="flex-1">{children}</main>
        {footer && <footer className="py-4 text-center text-sm text-textMuted">{footer}</footer>}
      </div>
    </div>
  );
};

export default AppLayout;
