import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse, Cohort } from '@/shared/types';
import type { OnboardingPayload, OnboardingResponse } from '../types';
import type {
  MyPageResponse,
  MyPageUpdateRequest,
  NicknameChangeRequest,
  NicknameChangeResponse,
  PasswordChangeRequest,
  PasswordChangeResponse,
  ProfileImageCompleteRequest,
  ProfileImageCompleteResponse,
  ProfileImageDeleteResponse,
  ProfileImagePresignRequest,
  ProfileImagePresignResponse,
  WithdrawRequest,
  WithdrawResponse,
} from '../mypage/types';


export const fetchCohorts = async (): Promise<ApiResponse<Cohort[]>> => {
  return await axiosInstance.get('/auth/cohorts');
};


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

export const resetOnboarding = async (): Promise<ApiResponse<void>> => {
  return await axiosInstance.delete('/users/onboarding');
};

export const fetchMyPage = async (): Promise<ApiResponse<MyPageResponse>> => {
  return await axiosInstance.get('/users/me');
};

export const updateMyPage = async (
  payload: MyPageUpdateRequest
): Promise<ApiResponse<MyPageResponse>> => {
  return await axiosInstance.patch('/users/me', payload);
};

export const changeNickname = async (
  payload: NicknameChangeRequest
): Promise<ApiResponse<NicknameChangeResponse>> => {
  return await axiosInstance.patch('/users/me/nickname', payload);
};

export const createProfileImagePresign = async (
  payload: ProfileImagePresignRequest
): Promise<ApiResponse<ProfileImagePresignResponse>> => {
  return await axiosInstance.post('/users/me/profile-image/presign', payload);
};

export const completeProfileImage = async (
  payload: ProfileImageCompleteRequest
): Promise<ApiResponse<ProfileImageCompleteResponse>> => {
  return await axiosInstance.patch('/users/me/profile-image', payload);
};

export const deleteProfileImage = async (): Promise<ApiResponse<ProfileImageDeleteResponse>> => {
  return await axiosInstance.delete('/users/me/profile-image');
};

export const changePassword = async (
  payload: PasswordChangeRequest
): Promise<ApiResponse<PasswordChangeResponse>> => {
  return await axiosInstance.patch('/users/me/password', payload);
};

export const withdraw = async (
  payload: WithdrawRequest
): Promise<ApiResponse<WithdrawResponse>> => {
  return await axiosInstance.delete('/users/me', { data: payload });
};
