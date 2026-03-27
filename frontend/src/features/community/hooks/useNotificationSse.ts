import { useEffect } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useNotificationStore } from '../store/useNotificationStore';

export const useNotificationSse = (enabled: boolean) => {
    const token = useAuthStore((state) => state.accessToken);

    useEffect(() => {
        if (!enabled) {
            return;
        }

        if (!token) {
            return;
        }

        const API_BASE_URL =
            import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';
        const streamUrl = `${API_BASE_URL}/notifications/stream`;

        const eventSource = new (EventSourcePolyfill as any)(streamUrl, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
            withCredentials: true,
            heartbeatTimeout: 60 * 1000,
        });

        eventSource.addEventListener('connect', () => { });

        eventSource.addEventListener('heartbeat', () => { });

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

        eventSource.addEventListener('error', () => { });

        return () => {
            eventSource.close();
        };
    }, [enabled, token]);
};