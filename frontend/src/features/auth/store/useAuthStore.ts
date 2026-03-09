import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { UserProfile } from '@/features/auth/types';

interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  
  // Actions
  loginSuccess: (user: UserProfile) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,

      loginSuccess: (user: UserProfile) => {
        // 유저 프로필(Id, OnboardingCompleted, Role 등)을 저장합니다.
        // 토큰은 Cookie로 관리되거나 인터셉터에서 처리됨을 가정합니다.
        set({ isAuthenticated: true, user });
      },

      logout: () => {
        set({ isAuthenticated: false, user: null });
      },
    }),
    {
      name: 'auth-storage', // 이 이름으로 로컬스토리지에 전체 상태가 캐시(저장)됩니다.
      storage: createJSONStorage(() => localStorage), // (선택) session storage 사용 가능
    }
  )
);
