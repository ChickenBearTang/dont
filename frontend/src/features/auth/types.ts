// 회원가입, 로그인 시 등 여러 과정에서 쓰이는 타입들을 정의합니다.

export type UserRole = 'ROLE_USER' | 'ROLE_ADMIN';

export interface UserProfile {
  userId: number;
  nickname: string;
  onboardingCompleted: boolean;
  profileImageUrl?: string;
  role: UserRole;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: UserProfile;
}

export interface LoginRequestPayload {
  email: string;
  password: string;
}

export type LoginResponseData = UserProfile;

export interface SignUpRequestPayload {
  email: string;
  password?: string;
  name: string;
  birthDate: string;
  nickname: string;
  cohortId: number;
  termsAgreed: boolean;
}

export interface SignUpResponseData {
  userId: number;
  email: string;
  nickname: string;
  onboardingRequired: boolean;
  onboardingStatus: string;
  createdAt: string;
}
