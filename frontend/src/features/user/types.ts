export interface UserData {
  nickname: string;
  isKdt: boolean;
  housingExpense: number;
  monthlyFixedCost: number;
  goalAmount: number;
  connected: boolean;
}

/**
 * 온보딩 요청 데이터
 */
export interface OnboardingPayload {
  cohortId: number;
  goalAmount: number;
}

/**
 * 온보딩 응답 데이터
 */
export interface OnboardingResponse {
  success: boolean;
  onboardingCompleted: boolean;
}
