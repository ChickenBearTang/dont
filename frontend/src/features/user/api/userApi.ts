import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse, Cohort } from '@/shared/types';
import type { OnboardingPayload, OnboardingResponse } from '../types';
import type { MyPageResponse } from '../mypage/types';

/**
 * 기수(Cohort) 목록 조회 API
 * 주로 회원가입 혹은 개인정보 설정 등에서 전체 기수 목록을 그리기 위해 호출됩니다.
 * @returns 기수 목록
 */
export const fetchCohorts = async (): Promise<ApiResponse<Cohort[]>> => {
  return await axiosInstance.get('/auth/cohorts');
};

/**
 * 온보딩 정보 제출 API
 */
export const submitOnboarding = async (
  payload: OnboardingPayload
): Promise<ApiResponse<OnboardingResponse>> => {
  return await axiosInstance.post('/users/onboarding', payload);
};

export const fetchOnboardingStatus = async (): Promise<ApiResponse<OnboardingResponse>> => {
  return await axiosInstance.get('/users/onboarding/status');
};

export const completeOnboarding = async (): Promise<ApiResponse<OnboardingResponse>> => {
  return await axiosInstance.post('/users/onboarding/complete');
};

export const fetchMyPage = async (): Promise<ApiResponse<MyPageResponse>> => {
  return await axiosInstance.get('/users/me');
};
