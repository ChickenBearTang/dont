import { create } from 'zustand';
import type { UserProfile } from '@/features/auth/types';

interface AuthState {
  accessToken: string | null;
  isAuthenticated: boolean;
  isAuthInitializing: boolean;
  user: UserProfile | null;

  setAuthInitializing: (isInitializing: boolean) => void;
  setAccessToken: (accessToken: string | null) => void;
  loginSuccess: (params: { accessToken: string; user: UserProfile | null }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  isAuthenticated: false,
  isAuthInitializing: true,
  user: null,

  setAuthInitializing: (isAuthInitializing) => set({ isAuthInitializing }),

  setAccessToken: (accessToken) =>
    set({
      accessToken,
      isAuthenticated: !!accessToken,
    }),

  loginSuccess: ({ accessToken, user }) =>
    set({
      accessToken,
      isAuthenticated: true,
      user,
    }),

  logout: () =>
    set({
      accessToken: null,
      isAuthenticated: false,
      user: null,
    }),
}));
