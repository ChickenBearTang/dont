import type { UserProfile } from '@/features/auth/types';

const AUTH_USER_KEY = 'auth_user';

export const saveAuthUser = (user: UserProfile | null) => {
  if (!user) {
    sessionStorage.removeItem(AUTH_USER_KEY);
    return;
  }

  sessionStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
};

export const loadAuthUser = (): UserProfile | null => {
  const raw = sessionStorage.getItem(AUTH_USER_KEY);

  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    sessionStorage.removeItem(AUTH_USER_KEY);
    return null;
  }
};

export const clearAuthUser = () => {
  sessionStorage.removeItem(AUTH_USER_KEY);
};
