export interface UserData {
  nickname: string;
  isKdt: boolean;
  housingExpense: number;
  monthlyFixedCost: number;
  goalAmount: number;
  connected: boolean;
}

export interface OnboardingPayload {
  cohortId: number;
  goalAmount: number;
}

export interface OnboardingResponse {
  success: boolean;
  onboardingCompleted: boolean;
}
