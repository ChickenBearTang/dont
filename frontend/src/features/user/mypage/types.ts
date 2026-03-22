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
