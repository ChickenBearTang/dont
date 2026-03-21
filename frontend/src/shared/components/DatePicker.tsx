import { forwardRef, useId, type InputHTMLAttributes } from 'react';

interface DatePickerProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: boolean;
  errorMessage?: string;
  inputClassName?: string;
}

const baseDateClassName =
  'w-full rounded-[18px] border bg-surface-base px-5 py-[15px] text-[15px] font-semibold text-text-strong shadow-[0_1px_0_rgba(255,255,255,0.65)_inset] transition-all duration-200 focus:outline-none disabled:cursor-not-allowed disabled:bg-surface-soft';

export const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(
  (
    { label, hint, error, errorMessage, className = '', inputClassName = '', id, ...props },
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
        <div className="relative">
          <input
            ref={ref}
            id={inputId}
            type="date"
            aria-invalid={error ? 'true' : 'false'}
            className={`${baseDateClassName} ${
              error
                ? 'border-danger-strong bg-surface-danger focus:border-danger-strong focus:ring-4 focus:ring-danger-soft'
                : 'border-line-soft focus:border-accent focus:ring-4 focus:ring-accent-soft'
            } ${inputClassName}
            [&::-webkit-calendar-picker-indicator]:cursor-pointer
            [&::-webkit-calendar-picker-indicator]:opacity-60
            hover:[&::-webkit-calendar-picker-indicator]:opacity-100`}
            {...props}
          />
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

DatePicker.displayName = 'DatePicker';
