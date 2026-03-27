import { useEffect } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { refreshAccessToken } from '@/features/auth/api/authApi';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useNotificationStore } from '../store/useNotificationStore';

const REFRESH_COOLDOWN_MS = 10000;

const getStatusCode = (error: unknown): number | undefined => {
  if (typeof error !== 'object' || error === null || !('response' in error)) {
    return undefined;
  }

  return (error as { response?: { status?: number } }).response?.status;
};

export const useNotificationSse = (enabled: boolean) => {
  const token = useAuthStore((state) => state.accessToken);
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    if (!enabled || !token) {
      return;
    }

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';
    const streamUrl = `${apiBaseUrl}/notifications/stream`;

    let refreshInFlight = false;
    let lastRefreshAt = 0;

    const eventSource = new (EventSourcePolyfill as any)(streamUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      withCredentials: true,
      heartbeatTimeout: 60 * 1000,
    });

    eventSource.addEventListener('connect', (event: Event) => {
      console.log('Notification SSE connected:', (event as MessageEvent).data);
    });

    eventSource.addEventListener('notification-created', async () => {
      try {
        await Promise.all([
          useNotificationStore.getState().fetchUnreadCount(),
          useNotificationStore.getState().fetchNotifications(),
        ]);
      } catch (error) {
        console.error('Failed to refresh notifications after SSE event:', error);
      }
    });

    eventSource.addEventListener('error', async () => {
      const now = Date.now();

      if (refreshInFlight || now - lastRefreshAt < REFRESH_COOLDOWN_MS) {
        return;
      }

      refreshInFlight = true;
      lastRefreshAt = now;

      try {
        const response = await refreshAccessToken();
        const nextToken = response.data.accessToken;
        setAccessToken(nextToken);
        eventSource.close();
      } catch (error) {
        const statusCode = getStatusCode(error);
        if (statusCode === 401 || statusCode === 403) {
          logout();
          eventSource.close();
          return;
        }

        console.warn('Notification SSE token refresh skipped due to non-auth error:', error);
      } finally {
        refreshInFlight = false;
      }
    });

    return () => {
      eventSource.close();
    };
  }, [enabled, logout, setAccessToken, token]);
};
