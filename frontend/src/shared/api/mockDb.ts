import type { Cohort } from '@/shared/types';
import type { UserProfile, SignUpRequestPayload } from '@/features/auth/types';

class MockDatabase {
  private users: (UserProfile & { email: string })[] = [
    {
      userId: 1,
      nickname: '테스트유저',
      onboardingCompleted: false,
      role: 'ROLE_USER',
      email: 'test@test.com',
    },
  ];

  private cohorts: Cohort[] = [
    { cohortId: 1, cohortCode: '14기' },
    { cohortId: 2, cohortCode: '15기' },
    { cohortId: 3, cohortCode: '16기' },
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

  // 사용자 조회 (로그인 시뮬레이션)
  findUser(email: string): UserProfile | undefined {
    const user = this.users.find((u) => u.email === email);
    if (user) {
      return this.toUserProfile(user);
    }
    return undefined;
  }

  // 사용자 등록 (회원가입 시뮬레이션)
  registerUser(payload: SignUpRequestPayload): UserProfile {
    const newUser = {
      userId: this.users.length + 1,
      nickname: payload.nickname,
      onboardingCompleted: false,
      role: 'ROLE_USER' as const,
      email: payload.email,
    };
    this.users.push(newUser);

    return this.toUserProfile(newUser);
  }

  // 기수 목록 조회
  getCohorts(): Cohort[] {
    return this.cohorts;
  }
}

export const mockDb = new MockDatabase();
