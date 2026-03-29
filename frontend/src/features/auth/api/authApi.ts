import axios from 'axios';
import axiosInstance from '@/shared/api/axiosInstance';
import type {
  EmailAvailabilityResponseData,
  EmailVerificationConfirmPayload,
  EmailVerificationConfirmResponseData,
  EmailVerificationSendPayload,
  EmailVerificationSendResponseData,
  LoginRequestPayload,
  LoginResponseData,
  PasswordResetConfirmPayload,
  PasswordResetConfirmResponseData,
  PasswordResetRequestPayload,
  PasswordResetRequestResponseData,
  SignUpRequestPayload,
  SignUpResponseData,
  TokenReissueResponseData,
  UserProfile,
} from '@/features/auth/types';
import type { ApiResponse } from '@/shared/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 10000;

const authClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

export const mapUserProfileFromLogin = (data: LoginResponseData): UserProfile => ({
  userId: data.userId,
  email: data.email,
  role: data.userRole,
  cohortId: data.cohortId,
  nickname: undefined,
  onboardingCompleted: undefined,
});

export const login = async (data: LoginRequestPayload): Promise<ApiResponse<LoginResponseData>> => {
  return await axiosInstance.post('/auth/login', data);
};

export const refreshAccessToken = async (): Promise<ApiResponse<TokenReissueResponseData>> => {
  const response = await authClient.post<ApiResponse<TokenReissueResponseData>>(
    '/auth/reissue',
    {}
  );
  return response.data;
};

export const logout = async (): Promise<void> => {
  await authClient.post('/auth/logout', {});
};

export const signup = async (
  data: SignUpRequestPayload
): Promise<ApiResponse<SignUpResponseData>> => {
  return await axiosInstance.post('/auth/signup', data);
};

export const sendEmailVerificationCode = async (
  data: EmailVerificationSendPayload
): Promise<ApiResponse<EmailVerificationSendResponseData>> => {
  return await axiosInstance.post('/auth/email-verification/send', data);
};

export const confirmEmailVerificationCode = async (
  data: EmailVerificationConfirmPayload
): Promise<ApiResponse<EmailVerificationConfirmResponseData>> => {
  return await axiosInstance.post('/auth/email-verification/confirm', data);
};

export const checkEmailAvailability = async (
  email: string
): Promise<ApiResponse<EmailAvailabilityResponseData>> => {
  return await axiosInstance.get('/auth/check-email', {
    params: { email },
  });
};

export const requestPasswordReset = async (
  data: PasswordResetRequestPayload
): Promise<ApiResponse<PasswordResetRequestResponseData>> => {
  return await axiosInstance.post('/auth/password-reset/request', data);
};

export const confirmPasswordReset = async (
  data: PasswordResetConfirmPayload
): Promise<ApiResponse<PasswordResetConfirmResponseData>> => {
  return await axiosInstance.post('/auth/password-reset/confirm', data);
};
