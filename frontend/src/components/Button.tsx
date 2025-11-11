import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';
import clsx from 'clsx';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type ButtonSize = 'base' | 'sm';

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    fullWidth?: boolean;
    size?: ButtonSize;
  }
>;

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'relative overflow-hidden border border-primaryGlow bg-gradient-to-r from-primary to-accent text-white shadow-glow before:absolute before:inset-0 before:-translate-x-full before:bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.25),transparent)] before:transition-transform before:duration-700 hover:shadow-glow hover:before:translate-x-full focus-visible:shadow-glow',
  secondary:
    'border border-borderStrong bg-surface/40 text-text transition-all duration-350 ease-out-soft hover:bg-surface/70 hover:shadow-card',
  danger:
    'border border-danger/30 bg-gradient-to-r from-danger/85 via-danger to-danger/80 text-white shadow-card hover:shadow-glow',
  ghost:
    'border border-transparent bg-transparent text-textSecondary transition-colors hover:border-borderStrong hover:text-text',
};

const sizeClasses: Record<ButtonSize, string> = {
  base: 'px-4 py-2 text-sm',
  sm: 'px-3 py-1 text-xs',
};

const Button = ({ variant = 'primary', fullWidth = false, size = 'base', className, children, ...props }: ButtonProps) => {
  return (
    <button
      className={clsx(
        'relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-lg font-semibold text-sm transition-all duration-350 ease-out-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-60',
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
