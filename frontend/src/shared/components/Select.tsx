import { forwardRef, useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import type { SelectOption } from '@/shared/types';

interface SelectProps {
  label?: string;
  options: SelectOption[];
  placeholder?: string;
  hint?: string;
  error?: boolean;
  errorMessage?: string;
  inputClassName?: string;
  className?: string;
  id?: string;
  name?: string;
  value?: string | number;
  disabled?: boolean;
  required?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  onChange?: (value: string) => void;
}

const baseTriggerClassName =
  'flex w-full items-center justify-between gap-3 rounded-[16px] border bg-surface-muted px-4 py-[15px] text-left text-[15px] font-semibold shadow-[0_10px_24px_rgba(15,23,42,0.04)] transition-all duration-200 hover:border-line-strong focus:outline-none disabled:cursor-not-allowed disabled:border-line-soft disabled:bg-surface-soft';

export const Select = forwardRef<HTMLButtonElement, SelectProps>(
  (
    {
      label,
      options,
      placeholder = '항목을 선택하세요',
      hint,
      error,
      errorMessage,
      className = '',
      inputClassName = '',
      id,
      name,
      value,
      disabled = false,
      searchable = false,
      searchPlaceholder = '검색어를 입력하세요',
      onChange,
    },
    ref
  ) => {
    const generatedId = useId();
    const selectId = id ?? generatedId;
    const listboxId = `${selectId}-listbox`;
    const rootRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [highlightedIndex, setHighlightedIndex] = useState(0);

    const message = error ? errorMessage : hint;
    const normalizedValue = value == null ? '' : String(value);

    const filteredOptions = useMemo(() => {
      const keyword = searchTerm.trim().toLowerCase();
      if (!keyword) {
        return options;
      }

      return options.filter((option) => option.label.toLowerCase().includes(keyword));
    }, [options, searchTerm]);

    const selectedOption = useMemo(
      () => options.find((option) => String(option.value) === normalizedValue),
      [normalizedValue, options]
    );

    useEffect(() => {
      if (!isOpen) {
        return;
      }

      const handlePointerDown = (event: MouseEvent) => {
        if (!rootRef.current?.contains(event.target as Node)) {
          setIsOpen(false);
        }
      };

      document.addEventListener('mousedown', handlePointerDown);
      return () => document.removeEventListener('mousedown', handlePointerDown);
    }, [isOpen]);

    const openDropdown = () => {
      const selectedIndex = filteredOptions.findIndex(
        (option) => String(option.value) === normalizedValue
      );
      setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : 0);
      setIsOpen(true);

      if (searchable) {
        window.setTimeout(() => searchInputRef.current?.focus(), 0);
      }
    };

    const closeDropdown = () => {
      setIsOpen(false);
      if (searchTerm) {
        setSearchTerm('');
      }
    };

    const handleSelect = (nextValue: string) => {
      onChange?.(nextValue);
      closeDropdown();
    };

    const handleTriggerKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
      if (disabled) {
        return;
      }

      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openDropdown();
        return;
      }

      if (event.key === 'Escape') {
        closeDropdown();
      }
    };

    const handleListKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
      if (!filteredOptions.length) {
        if (event.key === 'Escape') {
          closeDropdown();
        }
        return;
      }

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setHighlightedIndex((prev) => Math.min(prev + 1, filteredOptions.length - 1));
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setHighlightedIndex((prev) => Math.max(prev - 1, 0));
      } else if (event.key === 'Enter') {
        event.preventDefault();
        handleSelect(String(filteredOptions[highlightedIndex].value));
      } else if (event.key === 'Escape') {
        event.preventDefault();
        closeDropdown();
      }
    };

    return (
      <div ref={rootRef} className={`mt-4 ${className}`}>
        {label && (
          <label
            htmlFor={selectId}
            className="mb-2.5 block text-[13px] font-bold tracking-[-0.01em] text-text-muted"
          >
            {label}
          </label>
        )}

        <input type="hidden" name={name} value={normalizedValue} />

        <div className="relative">
          <button
            ref={ref}
            id={selectId}
            type="button"
            aria-haspopup="listbox"
            aria-expanded={isOpen}
            aria-controls={listboxId}
            aria-invalid={error ? 'true' : 'false'}
            disabled={disabled}
            className={`${baseTriggerClassName} ${
              error
                ? 'border-danger-strong bg-surface-danger focus:border-danger-strong focus:bg-surface-base focus:ring-4 focus:ring-danger-soft'
                : 'border-transparent focus:border-accent focus:bg-surface-base focus:ring-4 focus:ring-accent-soft'
            } ${inputClassName}`}
            onClick={() => (isOpen ? closeDropdown() : openDropdown())}
            onKeyDown={handleTriggerKeyDown}
          >
            <span className={selectedOption ? 'text-text-strong' : 'text-text-subtle'}>
              {selectedOption?.label ?? placeholder}
            </span>
            <span className="flex h-9 w-9 items-center justify-center rounded-[12px] bg-surface-base text-text-muted shadow-[0_4px_12px_rgba(15,23,42,0.06)]">
              <svg
                className={`h-5 w-5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
              </svg>
            </span>
          </button>

          {isOpen && (
            <div
              className="absolute left-0 right-0 top-[calc(100%+10px)] z-50 overflow-hidden rounded-[20px] border border-line-soft bg-surface-base shadow-[0_20px_50px_rgba(15,23,42,0.16)]"
              onKeyDown={handleListKeyDown}
            >
              {searchable && (
                <div className="border-b border-line-soft p-3">
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder={searchPlaceholder}
                    className="w-full rounded-[12px] border border-transparent bg-surface-muted px-3.5 py-2.5 text-[14px] font-medium text-text-strong placeholder:text-text-subtle focus:border-accent focus:bg-surface-base focus:outline-none"
                  />
                </div>
              )}

              <div
                id={listboxId}
                role="listbox"
                aria-activedescendant={
                  filteredOptions[highlightedIndex]
                    ? `${selectId}-option-${highlightedIndex}`
                    : undefined
                }
                tabIndex={-1}
                className="max-h-64 overflow-y-auto p-2"
              >
                {filteredOptions.length === 0 ? (
                  <div className="px-3 py-8 text-center text-[14px] font-medium text-text-subtle">
                    검색 결과가 없습니다.
                  </div>
                ) : (
                  filteredOptions.map((option, index) => {
                    const optionValue = String(option.value);
                    const isSelected = optionValue === normalizedValue;
                    const isHighlighted = index === highlightedIndex;

                    return (
                      <button
                        key={optionValue}
                        id={`${selectId}-option-${index}`}
                        type="button"
                        role="option"
                        aria-selected={isSelected}
                        className={`flex w-full items-center justify-between rounded-[14px] px-3.5 py-3 text-left text-[14px] font-semibold transition-colors ${
                          isSelected
                            ? 'bg-accent-soft text-accent'
                            : isHighlighted
                              ? 'bg-surface-muted text-text-strong'
                              : 'text-text-strong hover:bg-surface-muted'
                        }`}
                        onMouseEnter={() => setHighlightedIndex(index)}
                        onClick={() => handleSelect(optionValue)}
                      >
                        <span>{option.label}</span>
                        {isSelected && (
                          <svg
                            className="h-4 w-4 text-accent"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.704 5.29a1 1 0 010 1.42l-7.22 7.22a1 1 0 01-1.415 0l-3.372-3.372a1 1 0 111.414-1.414l2.665 2.664 6.513-6.513a1 1 0 011.415 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {message && (
          <p
            className={`mt-2 text-[12px] font-semibold ${error ? 'text-danger' : 'text-text-muted'}`}
          >
            {message}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
