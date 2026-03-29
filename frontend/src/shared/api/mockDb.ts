import type { Cohort } from '@/shared/types';
import type { UserProfile, SignUpRequestPayload } from '@/features/auth/types';

class MockDatabase {
  private users: (UserProfile & { email: string })[] = [
    {
      userId: 1,
      nickname: '테스트유저',
      onboardingCompleted: false,
      role: 'USER',
      email: 'test@test.com',
    },
  ];

  private cohorts: Cohort[] = [
    { cohortId: 1, cohortCode: '14기', generationNo: 14 },
    { cohortId: 2, cohortCode: '15기', generationNo: 15 },
    { cohortId: 3, cohortCode: '16기', generationNo: 16 },
  ];

  private toUserProfile(user: UserProfile & { email: string }): UserProfile {
    return {
      userId: user.userId,
      nickname: user.nickname,
      onboardingCompleted: user.onboardingCompleted,
      role: user.role,
      cohortId: user.cohortId,
    };
  }

  findUser(email: string): UserProfile | undefined {
    const user = this.users.find((u) => u.email === email);
    if (user) {
      return this.toUserProfile(user);
    }
    return undefined;
  }

  registerUser(payload: SignUpRequestPayload): UserProfile {
    const newUser = {
      userId: this.users.length + 1,
      nickname: payload.name,
      onboardingCompleted: false,
      role: 'USER' as const,
      email: payload.email,
    };
    this.users.push(newUser);

    return this.toUserProfile(newUser);
  }

  getCohorts(): Cohort[] {
    return this.cohorts;
  }
}

export const mockDb = new MockDatabase();
