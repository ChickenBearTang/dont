export interface MyPageResponse {
  userId: number;
  email: string;
  name: string | null;
  nickname: string;
  birthDate: string | null;
  profileImageUrl: string | null;
  onboardingStatus: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  monthlySavingGoalAmount: number | null;
  cohortId: number | null;
  cohortGenerationNo: number | null;
}

export interface MyPageUpdateRequest {
  name?: string;
  birthDate?: string | null;
  monthlySavingGoalAmount?: number;
}

export interface NicknameChangeRequest {
  nickname: string;
}

export interface NicknameChangeResponse {
  userId: number;
  nickname: string;
}
