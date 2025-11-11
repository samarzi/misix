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
  primary: 'bg-primary text-white border border-primary hover:bg-primary/90',
  secondary: 'bg-surfaceAlt text-text border border-border hover:bg-surface',
  danger: 'bg-danger text-white border border-danger hover:bg-danger/90',
  ghost: 'bg-transparent text-text border border-transparent hover:border-border',
};

const sizeClasses: Record<ButtonSize, string> = {
  base: 'px-4 py-2 text-sm',
  sm: 'px-3 py-1 text-xs',
};

const Button = ({ variant = 'primary', fullWidth = false, size = 'base', className, children, ...props }: ButtonProps) => {
  return (
    <button
      className={clsx(
        'rounded-md font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
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
