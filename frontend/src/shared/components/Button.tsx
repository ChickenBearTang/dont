import type { ButtonHTMLAttributes, Ref } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'oauth';
  ref?: Ref<HTMLButtonElement>;
}

export const Button = ({ children, variant = 'primary', className = '', ref, ...props }: ButtonProps) => {
  const baseClass =
    variant === 'primary'
      ? 'w-full bg-primary-blue text-white py-4 rounded-xl font-bold text-[17px] border-none shadow-[0_4px_14px_rgba(10,101,255,0.3)] hover:bg-[#0052cc] hover:-translate-y-0.5 active:bg-[#0040a8] transition-all disabled:bg-[#c2d7fa] disabled:cursor-not-allowed'
      : variant === 'outline'
        ? 'w-full bg-white text-primary-blue py-3.5 rounded-xl font-bold text-[16px] border-[1.5px] border-primary-blue hover:bg-[#f0f6ff] transition-all'
        : variant === 'oauth'
          ? 'w-full py-4 rounded-xl font-bold text-[16px] border-none shadow-sm flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all'
          : '';

  return (
    <button className={`${baseClass} ${className}`} {...props}>
      {children}
    </button>
  );
};
