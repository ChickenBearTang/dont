export type UserRole = 'ROLE_USER' | 'ROLE_ADMIN';

export interface UserProfile {
  userId: number;
  email?: string;
  nickname?: string;
  onboardingCompleted?: boolean;
  profileImageUrl?: string;
  role: UserRole;
  cohortId?: number;
}

export interface LoginRequestPayload {
  email: string;
  password: string;
}

export interface LoginResponseData {
  userId: number;
  email: string;
  userRole: UserRole;
  accessToken: string;
  tokenType: string;
  expiresInSeconds: number;
  cohortId?: number;
}

export interface TokenReissueResponseData {
  accessToken: string;
  tokenType: string;
  expiresInSeconds: number;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: UserProfile;
}

export interface SignUpRequestPayload {
  email: string;
  password?: string;
  realName: string;
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
