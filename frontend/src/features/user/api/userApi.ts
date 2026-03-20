import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse, Cohort } from '@/shared/types';
import type { OnboardingPayload, OnboardingResponse } from '../types';

export const fetchCohorts = async (): Promise<ApiResponse<Cohort[]>> => {
  return await axiosInstance.get('/auth/cohorts');
};

export const submitOnboarding = async (
  data: OnboardingPayload
): Promise<ApiResponse<OnboardingResponse>> => {
  return await axiosInstance.post('/users/onboarding', data);
};
