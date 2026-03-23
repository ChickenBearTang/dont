import { useId, type InputHTMLAttributes } from 'react';

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  hint?: string;
  error?: boolean;
  errorMessage?: string;
}

export const Checkbox = ({
  label,
  hint,
  error,
  errorMessage,
  className = '',
  id,
  ...props
}: CheckboxProps) => {
  const generatedId = useId();
  const elementId = id || generatedId;
  const message = error ? errorMessage : hint;

  return (
    <div className={`mt-4 ${className}`}>
      <div className="flex items-start gap-3">
        <div className="relative flex items-center h-6">
          <input
            type="checkbox"
            id={elementId}
            aria-invalid={error ? 'true' : 'false'}
            className={`peer h-5 w-5 shrink-0 appearance-none rounded-[7px] border bg-white transition-colors cursor-pointer ${
              error
                ? 'border-danger-strong bg-surface-danger focus:ring-4 focus:ring-danger-soft'
                : 'border-line-soft focus:ring-4 focus:ring-accent-soft'
            } checked:bg-accent checked:border-accent focus:outline-none`}
            {...props}
          />
          <svg
            className="pointer-events-none absolute left-1/2 top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 opacity-0 text-white transition-opacity duration-200 peer-checked:opacity-100"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        {label && (
          <label
            htmlFor={elementId}
            className="cursor-pointer select-none pt-0.5 text-[14px] font-semibold leading-6 text-text-muted"
          >
            {label}
          </label>
        )}
      </div>
      {message && (
        <p
          className={`mt-2 ml-8 text-[12px] font-semibold ${error ? 'text-danger' : 'text-text-muted'}`}
        >
          {message}
        </p>
      )}
    </div>
  );
};
