import type { InputHTMLAttributes, Ref } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  unit?: string;
  error?: boolean;
  ref?: Ref<HTMLInputElement>;
}

export const Input = ({ label, unit, error, className = '', ref, ...props }: InputProps) => (
  <div className={`mt-4 ${className}`}>
    {label && (
      <label className="font-extrabold text-[15px] text-eel">{label}</label>
    )}
    <div className={`mt-2 ${unit ? 'relative' : ''}`}>
      <input
        className={`w-full bg-[#f4f7fa] border border-transparent rounded-[14px] px-5 py-4 text-[16px] text-eel placeholder-[#a0aabf] font-semibold transition-colors focus:outline-none focus:border-primary-blue focus:bg-white focus:shadow-[0_0_0_4px_var(--blue-bg)] ${
          error ? '!border-error-red !bg-[#ffeeee]' : ''
        }`}
        {...props}
        style={unit ? { paddingRight: '3rem' } : undefined}
      />
      {unit && (
        <span className="absolute right-5 top-1/2 -translate-y-1/2 font-bold text-gray">
          {unit}
        </span>
      )}
    </div>
  </div>
);
