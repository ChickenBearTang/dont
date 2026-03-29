import axiosInstance from '@/shared/api/axiosInstance';
import type {
  SpendingSummaryResponse,
  AiReportResponse,
  CardRecommendationResponse,
  CohortComparisonResponse,
} from '../types';

export const getSpendingSummary = async (
  startDate: string,
  endDate: string,
  includeAi = false
): Promise<SpendingSummaryResponse> => {
  return await axiosInstance.get('/fin/cards/spending-summary', {
    params: { startDate, endDate, includeAi },
    timeout: 120000,
  });
};

export const getMonthlyAiReport = async (reportMonth: string): Promise<AiReportResponse> => {
  return await axiosInstance.get('/fin/consumption/reports/monthly', {
    params: { reportMonth },
    timeout: 120000,
  });
};

export const generateMonthlyAiReport = async (reportMonth: string): Promise<AiReportResponse> => {
  return await axiosInstance.post(
    '/fin/consumption/reports/monthly',
    { reportMonth },
    { timeout: 120000 }
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
    { timeout: 120000 }
  );
};

export const regenerateAiReport = async (reportMonth: string): Promise<AiReportResponse> => {
  return await axiosInstance.post(
    '/fin/consumption/reports/monthly',
    {
      reportMonth,
    },
    { timeout: 120000 }
  );
};

export const getCardRecommendation = async (month: string): Promise<CardRecommendationResponse> => {
  const res: any = await axiosInstance.get('/fin/cards/recommend', {
    params: { month },
    timeout: 120000,
  });
  return res?.data ?? res;
};

export const getConsumptionCompare = async (): Promise<CohortComparisonResponse> => {
  return await axiosInstance.get('/fin/consumption/reports/compare', {
    timeout: 120000,
  });
};
