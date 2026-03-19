import axiosInstance from '@/shared/api/axiosInstance';
import type {
  LoginRequestPayload,
  AuthResponse,
  SignUpRequestPayload,
  SignUpResponseData,
  LoginResponseData,
} from '@/features/auth/types';
import type { ApiResponse } from '@/shared/types';

/**
 * 로그인 요청 API
 * @param data 이메일, 비밀번호
 * @returns JWT 토큰 및 유저 정보
 */
export const login = async (data: LoginRequestPayload): Promise<ApiResponse<LoginResponseData>> => {
  return await axiosInstance.post('/auth/login', data);
};

/**
 * 카카오 소셜 로그인 요청 API (예시)
 */
export const loginWithKakao = async (authCode: string): Promise<AuthResponse> => {
  return await axiosInstance.post('/auth/kakao', { code: authCode });
};

/**
 * 회원가입 API
 * @param data 이메일, 패스워드, 이름, 닉네임, 생년월일 등
 * @returns 회원가입 성공 결과 데이터
 */
export const signup = async (
  data: SignUpRequestPayload
): Promise<ApiResponse<SignUpResponseData | null>> => {
  return await axiosInstance.post('/auth/signup', data);
};
