import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  unit?: string;
  hint?: string;
  hintTone?: 'default' | 'success';
  error?: boolean;
  errorMessage?: string;
  inputClassName?: string;
  endAdornment?: ReactNode;
}

const baseInputClassName =
  'w-full rounded-[20px] px-5 py-[16px] text-[16px] font-bold text-eel placeholder:text-text-subtle transition-all duration-300 outline-none ring-0 disabled:cursor-not-allowed disabled:opacity-60 border border-transparent';

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      unit,
      hint,
      hintTone = 'default',
      error,
      errorMessage,
      className = '',
      inputClassName = '',
      endAdornment,
      id,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = id ?? generatedId;
    const message = error ? errorMessage : hint;
    const hasTrailingAdornment = !!unit || !!endAdornment;

    return (
      <div className={`flex flex-col gap-1.5 ${className}`}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-[14px] font-black tracking-tight text-text-strong ml-1"
          >
            {label}
          </label>
        )}
        <div className={unit || endAdornment ? 'relative flex items-center' : 'relative'}>
          <input
            ref={ref}
            id={inputId}
            aria-invalid={error ? 'true' : 'false'}
            className={`${baseInputClassName} ${error
              ? 'bg-error-red/5 ring-2 ring-error-red focus:bg-white focus:shadow-[0_4px_24px_rgba(255,59,48,0.15)]'
              : 'bg-[#eaeff5] shadow-[inset_0_2px_8px_rgba(15,23,42,0.06)] focus:bg-white focus:ring-1 focus:ring-primary-blue focus:border-primary-blue focus:shadow-[0_4px_24px_rgba(10,101,255,0.08)] hover:bg-[#dfe5f0]'
              } ${inputClassName}`}
            {...props}
            style={hasTrailingAdornment ? { paddingRight: '3.5rem' } : undefined}
          />
          {unit && (
            <span className="pointer-events-none absolute right-5 text-[15px] font-black text-text-muted">
              {unit}
            </span>
          )}
          {endAdornment && !unit && (
            <div className="absolute inset-y-0 right-4 flex items-center text-text-subtle">
              {endAdornment}
            </div>
          )}
        </div>
        {message && (
          <p
            className={`mt-1 text-[13px] font-bold ml-1 ${error ? 'text-error-red' : hintTone === 'success' ? 'text-success' : 'text-text-muted'
              }`}
          >
            {message}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

Input.displayName = 'Input';
