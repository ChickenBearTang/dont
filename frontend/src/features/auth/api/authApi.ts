import axios from 'axios';
import axiosInstance from '@/shared/api/axiosInstance';
import type {
  LoginRequestPayload,
  LoginResponseData,
  SignUpRequestPayload,
  SignUpResponseData,
  TokenReissueResponseData,
  UserProfile,
} from '@/features/auth/types';
import type { ApiResponse } from '@/shared/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';
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
