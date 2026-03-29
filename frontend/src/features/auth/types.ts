export type UserRole = 'USER' | 'ADMIN';

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
  password: string;
  name: string;
  birthDate: string;
  cohortId: number;
  termsAgreed: boolean;
}

export type SignUpResponseData = null;

export interface EmailVerificationSendPayload {
  email: string;
}

export interface EmailVerificationSendResponseData {
  email: string;
  expiresInSeconds: number;
}

export interface EmailVerificationConfirmPayload {
  email: string;
  code: string;
}

export interface EmailVerificationConfirmResponseData {
  email: string;
  verified: boolean;
  verifiedExpiresInSeconds: number;
}

export interface EmailAvailabilityResponseData {
  email: string;
  available: boolean;
}

export interface PasswordResetRequestPayload {
  email: string;
}

export interface PasswordResetRequestResponseData {
  message: string;
  expiresInSeconds: number;
}

export interface PasswordResetConfirmPayload {
  email: string;
  code: string;
  newPassword: string;
}

export interface PasswordResetConfirmResponseData {
  resetCompleted: boolean;
}
