import { create } from 'zustand';
import type { UserProfile } from '@/features/auth/types';
import { clearAuthUser, loadAuthUser, saveAuthUser } from '@/features/auth/utils/authStorage';
<<<<<<< HEAD
=======
import { queryClient } from '@/shared/api/queryClient';
>>>>>>> 729f51fe1c1d02ebf2139bb96d47f748323db339

interface AuthState {
  accessToken: string | null;
  isAuthenticated: boolean;
  isAuthInitializing: boolean;
  user: UserProfile | null;

  setAuthInitializing: (isInitializing: boolean) => void;
  setAccessToken: (accessToken: string | null) => void;
  restoreSession: (params: { accessToken: string; user?: UserProfile | null }) => void;
  loginSuccess: (params: { accessToken: string; user: UserProfile | null }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  isAuthenticated: false,
  isAuthInitializing: true,
  user: loadAuthUser(),

  setAuthInitializing: (isAuthInitializing) => set({ isAuthInitializing }),

  setAccessToken: (accessToken) =>
    set((state) => ({
      accessToken,
      isAuthenticated: !!accessToken,
      user: state.user ?? loadAuthUser(),
    })),

  restoreSession: ({ accessToken, user }) => {
    const nextUser = user ?? loadAuthUser();

    if (nextUser) {
      saveAuthUser(nextUser);
    } else {
      clearAuthUser();
    }

    set({
      accessToken,
      isAuthenticated: !!accessToken,
      user: nextUser,
    });
  },

  loginSuccess: ({ accessToken, user }) => {
    if (user) {
      saveAuthUser(user);
    } else {
      clearAuthUser();
    }

    set({
      accessToken,
      isAuthenticated: true,
      user,
    });
  },

  logout: () => {
<<<<<<< HEAD
    clearAuthUser();
=======
    // 1. 보안을 위한 스토리지 및 전역 캐시 즉시 소거
    clearAuthUser();
    queryClient.clear();
>>>>>>> 729f51fe1c1d02ebf2139bb96d47f748323db339

    set({
      accessToken: null,
      isAuthenticated: false,
      user: null,
    });
  },
}));
