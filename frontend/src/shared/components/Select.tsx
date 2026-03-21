import { forwardRef, useId, type SelectHTMLAttributes } from 'react';
import type { SelectOption } from '@/shared/types';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  placeholder?: string;
  hint?: string;
  error?: boolean;
  errorMessage?: string;
  inputClassName?: string;
}

const baseSelectClassName =
  'w-full appearance-none rounded-[18px] border bg-surface-base px-5 py-[15px] pr-14 text-[15px] font-semibold shadow-[0_1px_0_rgba(255,255,255,0.65)_inset] transition-all duration-200 focus:outline-none disabled:cursor-not-allowed disabled:bg-surface-soft';

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      options,
      placeholder,
      hint,
      error,
      errorMessage,
      className = '',
      inputClassName = '',
      id,
      value,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const selectId = id ?? generatedId;
    const isEmpty = value === '' || value === undefined || value === null;
    const message = error ? errorMessage : hint;

    return (
      <div className={`mt-4 ${className}`}>
        {label && (
          <label
            htmlFor={selectId}
            className="mb-2 block text-[14px] font-extrabold tracking-[-0.01em] text-text-strong"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            value={value}
            aria-invalid={error ? 'true' : 'false'}
            className={`${baseSelectClassName} ${
              error
                ? 'border-danger-strong bg-surface-danger text-text-strong focus:border-danger-strong focus:ring-4 focus:ring-danger-soft'
                : 'border-line-soft focus:border-accent focus:ring-4 focus:ring-accent-soft'
            } ${isEmpty ? 'text-text-subtle' : 'text-text-strong'} ${inputClassName}`}
            {...props}
          >
            {placeholder && (
              <option value="" disabled hidden>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value} className="text-text-strong">
                {option.label}
              </option>
            ))}
          </select>

          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-5 text-text-subtle">
            <svg className="h-5 w-5 fill-current" viewBox="0 0 20 20" aria-hidden="true">
              <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
            </svg>
          </div>
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

Select.displayName = 'Select';
