import axiosInstance from '@/shared/api/axiosInstance';
import type { SpendingSummaryResponse, AiReportResponse } from '../types';

export const getSpendingSummary = async (
  startDate: string,
  endDate: string
): Promise<SpendingSummaryResponse> => {
  return await axiosInstance.get('/fin/cards/spending-summary', {
    params: { startDate, endDate },
  });
};

export const getMonthlyAiReport = async (reportMonth: string): Promise<AiReportResponse> => {
  return await axiosInstance.get('/fin/consumption/reports/monthly', {
    params: { reportMonth },
    timeout: 30000, // 30 seconds
  });
};

export const generateMonthlyAiReport = async (reportMonth: string): Promise<AiReportResponse> => {
  return await axiosInstance.post(
    '/fin/consumption/reports/monthly',
    { reportMonth },
    { timeout: 30000 } // 30 seconds
  );
};

export const sendAiJustification = async (
  targetMonth: string,
  message: string
): Promise<unknown> => {
  return await axiosInstance.post(
    '/fin/consumption/reports/justifications/evaluate',
    {
      target_month: targetMonth,
      user_message: message,
    },
    { timeout: 30000 }
  );
};

export const regenerateAiReport = async (reportMonth: string): Promise<AiReportResponse> => {
  return await axiosInstance.post(
    '/fin/consumption/reports/monthly',
    {
      reportMonth,
    },
    { timeout: 30000 }
  );
};

