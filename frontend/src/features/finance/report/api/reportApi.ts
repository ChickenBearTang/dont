import axiosInstance from '@/shared/api/axiosInstance';
import type { SpendingSummaryResponse } from '../types';

export const getSpendingSummary = async (
  startDate: string,
  endDate: string
): Promise<SpendingSummaryResponse> => {
  return await axiosInstance.get('/fin/cards/spending-summary', {
    params: { startDate, endDate },
  });
};
