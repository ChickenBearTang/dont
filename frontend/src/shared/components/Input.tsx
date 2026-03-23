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
  'w-full rounded-[16px] border bg-surface-muted px-4 py-[15px] text-[15px] font-semibold text-text-strong placeholder:text-text-subtle shadow-[0_10px_24px_rgba(15,23,42,0.04)] transition-all duration-200 hover:border-line-strong focus:outline-none disabled:cursor-not-allowed disabled:border-line-soft disabled:bg-surface-soft disabled:text-text-subtle';

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
      <div className={`mt-4 ${className}`}>
        {label && (
          <label
            htmlFor={inputId}
            className="mb-2.5 block text-[13px] font-bold tracking-[-0.01em] text-text-muted"
          >
            {label}
          </label>
        )}
        <div className={unit || endAdornment ? 'relative' : ''}>
          <input
            ref={ref}
            id={inputId}
            aria-invalid={error ? 'true' : 'false'}
            className={`${baseInputClassName} ${
              error
                ? 'border-danger-strong bg-surface-danger focus:border-danger-strong focus:bg-surface-base focus:ring-4 focus:ring-danger-soft'
                : 'border-transparent focus:border-accent focus:bg-surface-base focus:ring-4 focus:ring-accent-soft'
            } ${inputClassName}`}
            {...props}
            style={hasTrailingAdornment ? { paddingRight: '3.25rem' } : undefined}
          />
          {unit && (
            <span className="pointer-events-none absolute right-5 top-1/2 -translate-y-1/2 text-[13px] font-bold text-text-muted">
              {unit}
            </span>
          )}
          {endAdornment && !unit && (
            <div className="absolute inset-y-0 right-3 flex items-center text-text-subtle">
              {endAdornment}
            </div>
          )}
        </div>
        {message && (
          <p
            className={`mt-2 text-[12px] font-semibold ${
              error ? 'text-danger' : hintTone === 'success' ? 'text-success' : 'text-text-muted'
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
