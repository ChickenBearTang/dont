import axiosInstance from '@/shared/api/axiosInstance';
import type { SpendingSummaryResponse, AiReportResponse, CardRecommendationResponse } from '../types';

export const getSpendingSummary = async (
  startDate: string,
  endDate: string,
  includeAi = false
): Promise<SpendingSummaryResponse> => {
  return await axiosInstance.get('/fin/cards/spending-summary', {
    params: { startDate, endDate, includeAi },
    timeout: 30000, // 30 seconds
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
      targetMonth,
      message,
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

export const getCardRecommendation = async (month: string): Promise<CardRecommendationResponse> => {
  const res: any = await axiosInstance.get('/fin/cards/recommend', {
    params: { month },
  });
  return res?.data ?? res;
};
