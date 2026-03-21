import { useId, type InputHTMLAttributes } from 'react';

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
}

export const Checkbox = ({ label, className = '', id, ...props }: CheckboxProps) => {
  const generatedId = useId();
  const elementId = id || generatedId;

  return (
    <div className={`flex items-start gap-3 mt-4 ${className}`}>
      <div className="relative flex items-center h-6">
        <input
          type="checkbox"
          id={elementId}
          className="peer appearance-none w-5 h-5 bg-[#f4f7fa] border-[1.5px] border-[#d1d5db] rounded-[6px] shrink-0 checked:bg-primary-blue checked:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/30 transition-colors cursor-pointer"
          {...props}
        />
        <svg
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none opacity-0 peer-checked:opacity-100 text-white transition-opacity duration-200"
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
          className="text-[15px] font-medium text-[#4a5568] cursor-pointer pt-0.5 select-none hover:text-eel transition-colors"
        >
          {label}
        </label>
      )}
    </div>
  );
};
