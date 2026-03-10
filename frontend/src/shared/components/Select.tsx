import type { SelectHTMLAttributes, Ref } from 'react';
import type { SelectOption } from '@/shared/types';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  placeholder?: string;
  error?: boolean;
  ref?: Ref<HTMLSelectElement>;
}

export const Select = ({ label, options, placeholder, error, className = '', ref, ...props }: SelectProps) => (
  <div className={`mt-4 ${className}`}>
    {label && (
      <label className="font-extrabold text-[15px] text-eel block mb-2">{label}</label>
    )}
    <div className="relative">
      <select
        className={`w-full bg-[#f4f7fa] border border-transparent rounded-[14px] px-5 py-4 text-[16px] text-eel font-semibold appearance-none transition-colors focus:outline-none focus:border-primary-blue focus:bg-white focus:shadow-[0_0_0_4px_var(--blue-bg)] disabled:opacity-60 disabled:cursor-not-allowed ${
          error ? '!border-error-red !bg-[#ffeeee]' : ''
        }`}
        {...props}
      >
        {placeholder && (
          <option value="" disabled className="text-[#a0aabf]">
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      
      {/* 화살표 아이콘 (커스텀) */}
      <div className="absolute inset-y-0 right-0 flex items-center px-5 pointer-events-none text-[#a0aabf]">
        <svg className="w-5 h-5 fill-current" viewBox="0 0 20 20">
          <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
        </svg>
      </div>
    </div>
  </div>
);
