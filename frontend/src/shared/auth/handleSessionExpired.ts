import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useUIStore } from '@/shared/store/useUIStore';

const SESSION_EXPIRED_TOAST_INTERVAL_MS = 5000;
let lastSessionExpiredToastAt = 0;

export const handleSessionExpired = () => {
  const now = Date.now();
  if (now - lastSessionExpiredToastAt > SESSION_EXPIRED_TOAST_INTERVAL_MS) {
    useUIStore
      .getState()
      .addToast('세션이 만료되었습니다. 다시 로그인해 주세요.', 'error');
    lastSessionExpiredToastAt = now;
  }

  useAuthStore.getState().logout();

  if (window.location.pathname !== '/login') {
    window.location.replace('/login');
  }
};
