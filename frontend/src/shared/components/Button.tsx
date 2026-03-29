import type { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'oauth' | 'ghost';
  fullWidth?: boolean;
}

const variantClassMap: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary:
    'bg-gradient-to-r from-primary-blue to-accent text-white shadow-[0_8px_20px_rgba(10,101,255,0.25)] hover:shadow-[0_12px_24px_rgba(10,101,255,0.35)] hover:-translate-y-[2px]',
  outline:
    'bg-white text-accent border-2 border-accent-soft hover:bg-accent-soft/30 hover:border-accent shadow-sm',
  oauth:
    'bg-white text-eel border border-line-soft shadow-sm hover:bg-surface-muted hover:shadow-md hover:-translate-y-[1px]',
  ghost: 'bg-transparent text-text-muted hover:text-accent hover:bg-accent-soft/50',
};

const disabledVariantClassMap: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'cursor-not-allowed bg-line-soft text-text-subtle shadow-none',
  outline:
    'cursor-not-allowed border-2 border-line-soft bg-surface-soft text-text-subtle shadow-none',
  oauth: 'cursor-not-allowed border-line-soft bg-surface-soft text-text-subtle shadow-none',
  ghost: 'cursor-not-allowed bg-transparent text-text-subtle shadow-none',
};

export const Button = ({
  children,
  variant = 'primary',
  fullWidth = true,
  className = '',
  disabled,
  ...props
}: ButtonProps) => {
  const toneClassName = disabled
    ? disabledVariantClassMap[variant]
    : `${variantClassMap[variant]} active:scale-[0.98]`;

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-[20px] px-6 py-[16px] text-[16px] font-black tracking-tight transition-all duration-300 ${
        fullWidth ? 'w-full' : ''
      } ${toneClassName} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
