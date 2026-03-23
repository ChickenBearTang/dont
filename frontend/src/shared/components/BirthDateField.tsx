import { forwardRef, useEffect, useId, useMemo, useRef, useState, type ChangeEvent } from 'react';

interface BirthDateFieldProps {
  label?: string;
  hint?: string;
  error?: boolean;
  errorMessage?: string;
  className?: string;
  value?: string;
  name?: string;
  disabled?: boolean;
  max?: string;
  min?: string;
  onChange?: (value: string) => void;
}

type SegmentType = 'year' | 'month' | 'day';

const segmentClassName =
  'w-full rounded-[12px] border border-line-soft bg-surface-base px-3 py-3 text-[15px] font-semibold text-text-strong shadow-[0_6px_18px_rgba(15,23,42,0.05)] transition-all duration-200 hover:border-line-strong focus:border-accent focus:outline-none focus:ring-4 focus:ring-accent-soft disabled:cursor-not-allowed disabled:bg-surface-soft disabled:text-text-subtle';

const parseDateValue = (value?: string) => {
  if (!value) {
    return { year: '', month: '', day: '' };
  }

  const [year = '', month = '', day = ''] = value.split('-');
  return { year, month, day };
};

const formatDateValue = (year: string, month: string, day: string) => {
  if (year.length !== 4 || !month || !day) {
    return '';
  }

  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
};

const clampNumber = (value: string, min: number, max: number) => {
  if (!value) return value;

  const parsed = Number(value);
  if (Number.isNaN(parsed)) return '';

  return String(Math.min(Math.max(parsed, min), max));
};

const getDaysInMonth = (year: string, month: string) => {
  const parsedYear = Number(year);
  const parsedMonth = Number(month);

  if (!parsedYear || !parsedMonth) {
    return 31;
  }

  return new Date(parsedYear, parsedMonth, 0).getDate();
};

const isValidDateString = (value: string, min?: string, max?: string) => {
  if (!value) return false;

  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(year, month - 1, day);

  if (
    Number.isNaN(date.getTime()) ||
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return false;
  }

  if (min && value < min) return false;
  if (max && value > max) return false;

  return true;
};

export const BirthDateField = forwardRef<HTMLInputElement, BirthDateFieldProps>(
  (
    {
      label,
      hint,
      error,
      errorMessage,
      className = '',
      value = '',
      name,
      disabled = false,
      min,
      max,
      onChange,
    },
    ref
  ) => {
    const generatedId = useId();
    const rootRef = useRef<HTMLDivElement>(null);
    const monthRef = useRef<HTMLInputElement>(null);
    const dayRef = useRef<HTMLInputElement>(null);

    const message = error ? errorMessage : hint;
    const parsedInitialValue = parseDateValue(value);
    const [year, setYear] = useState(parsedInitialValue.year);
    const [month, setMonth] = useState(parsedInitialValue.month);
    const [day, setDay] = useState(parsedInitialValue.day);
    const [openSegment, setOpenSegment] = useState<SegmentType | null>(null);

    useEffect(() => {
      if (!openSegment) return;

      const handlePointerDown = (event: MouseEvent) => {
        if (!rootRef.current?.contains(event.target as Node)) {
          setOpenSegment(null);
        }
      };

      document.addEventListener('mousedown', handlePointerDown);
      return () => document.removeEventListener('mousedown', handlePointerDown);
    }, [openSegment]);

    const maxDate = useMemo(() => (max ? new Date(max) : new Date()), [max]);
    const minDate = useMemo(
      () => (min ? new Date(min) : new Date(maxDate.getFullYear() - 100, 0, 1)),
      [maxDate, min]
    );

    const yearOptions = useMemo(() => {
      const values: string[] = [];
      for (let nextYear = maxDate.getFullYear(); nextYear >= minDate.getFullYear(); nextYear -= 1) {
        values.push(String(nextYear));
      }
      return values;
    }, [maxDate, minDate]);

    const monthOptions = useMemo(
      () => Array.from({ length: 12 }, (_, index) => String(index + 1).padStart(2, '0')),
      []
    );

    const dayOptions = useMemo(() => {
      const lastDay = getDaysInMonth(year, month);
      return Array.from({ length: lastDay }, (_, index) => String(index + 1).padStart(2, '0'));
    }, [month, year]);

    const emitValue = (nextYear: string, nextMonth: string, nextDay: string) => {
      const nextValue = formatDateValue(nextYear, nextMonth, nextDay);
      if (!nextValue) {
        onChange?.('');
        return;
      }

      onChange?.(isValidDateString(nextValue, min, max) ? nextValue : '');
    };

    const handleYearChange = (event: ChangeEvent<HTMLInputElement>) => {
      const nextYear = event.target.value.replace(/\D/g, '').slice(0, 4);
      setYear(nextYear);
      emitValue(nextYear, month, day);

      if (nextYear.length === 4) {
        monthRef.current?.focus();
      }
    };

    const handleMonthChange = (event: ChangeEvent<HTMLInputElement>) => {
      const digitsOnly = event.target.value.replace(/\D/g, '').slice(0, 2);
      const nextMonth = clampNumber(digitsOnly, 1, 12);
      setMonth(nextMonth);
      emitValue(year, nextMonth, day);

      if (digitsOnly.length === 2 || Number(nextMonth) > 1) {
        dayRef.current?.focus();
      }
    };

    const handleDayChange = (event: ChangeEvent<HTMLInputElement>) => {
      const digitsOnly = event.target.value.replace(/\D/g, '').slice(0, 2);
      const nextDay = clampNumber(digitsOnly, 1, 31);
      setDay(nextDay);
      emitValue(year, month, nextDay);
    };

    const selectSegmentValue = (segment: SegmentType, nextValue: string) => {
      if (segment === 'year') {
        setYear(nextValue);
        emitValue(nextValue, month, day);
        setOpenSegment(null);
        monthRef.current?.focus();
        return;
      }

      if (segment === 'month') {
        setMonth(nextValue);
        emitValue(year, nextValue, day);
        setOpenSegment(null);
        dayRef.current?.focus();
        return;
      }

      setDay(nextValue);
      emitValue(year, month, nextValue);
      setOpenSegment(null);
    };

    const stateClassName = error
      ? 'border-danger-strong bg-surface-danger focus:border-danger-strong focus:ring-danger-soft'
      : '';

    const renderOptionList = (segment: SegmentType, options: string[]) => (
      <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-50 max-h-[21rem] overflow-y-auto rounded-[14px] border border-line-soft bg-surface-base p-1.5 shadow-[0_16px_36px_rgba(15,23,42,0.14)] [scrollbar-width:thin] [scrollbar-color:var(--line-strong)_transparent] [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-line-strong [&::-webkit-scrollbar-track]:bg-transparent">
        {options.map((option) => {
          const isSelected =
            (segment === 'year' && option === year) ||
            (segment === 'month' && option === month) ||
            (segment === 'day' && option === day);

          return (
            <button
              key={option}
              type="button"
              className={`flex w-full items-center justify-between rounded-[10px] px-3 py-2 text-left text-[14px] font-semibold leading-6 transition-colors ${
                isSelected
                  ? 'bg-accent-soft text-accent'
                  : 'text-text-strong hover:bg-surface-muted'
              }`}
              onClick={() => selectSegmentValue(segment, option)}
            >
              <span>{option}</span>
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
        })}
      </div>
    );

    return (
      <div ref={rootRef} className={`mt-4 ${className}`}>
        {label && (
          <label className="mb-2.5 block text-[13px] font-bold tracking-[-0.01em] text-text-muted">
            {label}
          </label>
        )}

        <input type="hidden" name={name} value={value} />

        <div className="flex w-full items-center gap-2 rounded-[16px] border border-line-soft bg-surface-muted p-2">
          <div className="relative min-w-0 flex-[1.5]">
            <input
              ref={ref}
              id={`${generatedId}-year`}
              type="text"
              inputMode="numeric"
              placeholder="YYYY"
              maxLength={4}
              value={year}
              onChange={handleYearChange}
              onFocus={() => setOpenSegment('year')}
              onClick={() => setOpenSegment('year')}
              disabled={disabled}
              aria-invalid={error ? 'true' : 'false'}
              className={`${segmentClassName} ${stateClassName}`}
            />
            {openSegment === 'year' && renderOptionList('year', yearOptions)}
          </div>

          <div className="relative min-w-0 flex-1">
            <input
              ref={monthRef}
              id={`${generatedId}-month`}
              type="text"
              inputMode="numeric"
              placeholder="MM"
              maxLength={2}
              value={month}
              onChange={handleMonthChange}
              onFocus={() => setOpenSegment('month')}
              onClick={() => setOpenSegment('month')}
              disabled={disabled}
              aria-invalid={error ? 'true' : 'false'}
              className={`${segmentClassName} ${stateClassName}`}
            />
            {openSegment === 'month' && renderOptionList('month', monthOptions)}
          </div>

          <div className="relative min-w-0 flex-1">
            <input
              ref={dayRef}
              id={`${generatedId}-day`}
              type="text"
              inputMode="numeric"
              placeholder="DD"
              maxLength={2}
              value={day}
              onChange={handleDayChange}
              onFocus={() => setOpenSegment('day')}
              onClick={() => setOpenSegment('day')}
              disabled={disabled}
              aria-invalid={error ? 'true' : 'false'}
              className={`${segmentClassName} ${stateClassName}`}
            />
            {openSegment === 'day' && renderOptionList('day', dayOptions)}
          </div>
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

BirthDateField.displayName = 'BirthDateField';
