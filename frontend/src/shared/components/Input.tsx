import { forwardRef, useId, type InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  unit?: string;
  hint?: string;
  error?: boolean;
  errorMessage?: string;
  inputClassName?: string;
}

const baseInputClassName =
  'w-full rounded-[18px] border bg-surface-base px-5 py-[15px] text-[15px] font-semibold text-text-strong placeholder:text-text-subtle shadow-[0_1px_0_rgba(255,255,255,0.65)_inset] transition-all duration-200 focus:outline-none disabled:cursor-not-allowed disabled:bg-surface-soft disabled:text-text-subtle';

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    { label, unit, hint, error, errorMessage, className = '', inputClassName = '', id, ...props },
    ref
  ) => {
    const generatedId = useId();
    const inputId = id ?? generatedId;
    const message = error ? errorMessage : hint;

    return (
      <div className={`mt-4 ${className}`}>
        {label && (
          <label
            htmlFor={inputId}
            className="mb-2 block text-[14px] font-extrabold tracking-[-0.01em] text-text-strong"
          >
            {label}
          </label>
        )}
        <div className={unit ? 'relative' : ''}>
          <input
            ref={ref}
            id={inputId}
            aria-invalid={error ? 'true' : 'false'}
            className={`${baseInputClassName} ${
              error
                ? 'border-danger-strong bg-surface-danger focus:border-danger-strong focus:ring-4 focus:ring-danger-soft'
                : 'border-line-soft focus:border-accent focus:ring-4 focus:ring-accent-soft'
            } ${inputClassName}`}
            {...props}
            style={unit ? { paddingRight: '3.25rem' } : undefined}
          />
          {unit && (
            <span className="pointer-events-none absolute right-5 top-1/2 -translate-y-1/2 text-[13px] font-bold text-text-muted">
              {unit}
            </span>
          )}
        </div>
        {message && (
          <p
            className={`mt-2 text-[12px] font-semibold ${
              error ? 'text-danger' : 'text-text-muted'
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
