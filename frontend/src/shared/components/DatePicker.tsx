import type { InputHTMLAttributes, Ref } from 'react';

interface DatePickerProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: boolean;
  ref?: Ref<HTMLInputElement>;
}

export const DatePicker = ({ label, error, className = '', ref, ...props }: DatePickerProps) => (
  <div className={`mt-4 ${className}`}>
    {label && (
      <label className="font-extrabold text-[15px] text-eel block mb-2">{label}</label>
    )}
    <div className="relative">
      <input
        type="date"
        className={`w-full bg-[#f4f7fa] border border-transparent rounded-[14px] px-5 py-4 text-[16px] text-eel font-semibold transition-colors focus:outline-none focus:border-primary-blue focus:bg-white focus:shadow-[0_0_0_4px_var(--blue-bg)] ${
          error ? '!border-error-red !bg-[#ffeeee]' : ''
        }
        /* 네이티브 캘린더 아이콘 스타일링 (크롬/사파리 등) */
        [&::-webkit-calendar-picker-indicator]:cursor-pointer [&::-webkit-calendar-picker-indicator]:opacity-60 hover:[&::-webkit-calendar-picker-indicator]:opacity-100 transition-opacity`}
        {...props}
      />
    </div>
  </div>
);
