import { create } from 'zustand';
import type { UserProfile } from '@/features/auth/types';
import { clearAuthUser, loadAuthUser, saveAuthUser } from '@/features/auth/utils/authStorage';
import { queryClient } from '@/shared/api/queryClient';

interface AuthState {
  accessToken: string | null;
  isAuthenticated: boolean;
  isAuthInitializing: boolean;
  user: UserProfile | null;

  setAuthInitializing: (isInitializing: boolean) => void;
  setAccessToken: (accessToken: string | null) => void;
  restoreSession: (params: { accessToken: string; user?: UserProfile | null }) => void;
  loginSuccess: (params: { accessToken: string; user: UserProfile | null }) => void;
  updateUser: (user: Partial<UserProfile>) => void;
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

  updateUser: (partialUser) => {
    set((state) => {
      const nextUser = state.user ? { ...state.user, ...partialUser } : null;
      if (nextUser) {
        saveAuthUser(nextUser);
      }
      return { user: nextUser };
    });
  },

  logout: () => {

    clearAuthUser();
    queryClient.clear();

    set({
      accessToken: null,
      isAuthenticated: false,
      user: null,
    });
  },
}));
