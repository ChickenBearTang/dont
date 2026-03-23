import type { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'oauth' | 'ghost';
  fullWidth?: boolean;
}

const variantClassMap: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary:
    'bg-accent text-white border border-accent shadow-[0_14px_30px_rgba(37,99,235,0.24)] hover:bg-accent-strong hover:border-accent-strong',
  outline:
    'bg-surface-base text-accent border border-line-strong hover:bg-surface-muted hover:border-line-strong',
  oauth:
    'bg-surface-base text-text-strong border border-line-soft shadow-[0_10px_24px_rgba(15,23,42,0.06)] hover:bg-surface-soft',
  ghost: 'bg-transparent text-accent border border-transparent hover:bg-accent-soft',
};

const disabledVariantClassMap: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'cursor-not-allowed border-line-strong bg-line-strong text-accent-strong shadow-none',
  outline: 'cursor-not-allowed border-line-soft bg-surface-soft text-text-subtle shadow-none',
  oauth: 'cursor-not-allowed border-line-soft bg-surface-soft text-text-subtle shadow-none',
  ghost: 'cursor-not-allowed border-transparent bg-transparent text-text-subtle shadow-none',
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
    : `${variantClassMap[variant]} hover:-translate-y-[1px] active:translate-y-0`;

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-[18px] px-5 py-[14px] text-[15px] font-extrabold tracking-[-0.01em] transition-all duration-200 ${
        fullWidth ? 'w-full' : ''
      } ${toneClassName} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
