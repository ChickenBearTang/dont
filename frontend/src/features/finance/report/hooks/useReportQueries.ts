import { useQuery } from '@tanstack/react-query';
import { getSpendingSummary } from '../api/reportApi';


export const useSpendingSummary = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: ['spendingSummary', startDate, endDate],
    queryFn: () => getSpendingSummary(startDate, endDate, false),
    enabled: !!startDate && !!endDate,
  });
};


export const useCurrentMonthSpending = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  const format = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}${m}${d}`;
  };

  return useSpendingSummary(format(firstDay), format(lastDay));
};
