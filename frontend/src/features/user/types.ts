export interface UserData {
  nickname: string;
  isKdt: boolean;
  housingExpense: number;
  monthlyFixedCost: number;
  goalAmount: number;
  connected: boolean;
}


export interface OnboardingPayload {
  recommendedAmount: number;
}


export interface OnboardingResponse {
  onboardingStatus: string;
  onboardingCompleted: boolean;
  recommendedAmount: number | null;
}
