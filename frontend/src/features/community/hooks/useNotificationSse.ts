import { useEffect } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useNotificationStore } from '../store/useNotificationStore';

export const useNotificationSse = (enabled: boolean) => {
    useEffect(() => {
        if (!enabled) {
            return;
        }

        const token = useAuthStore.getState().accessToken;
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

        eventSource.addEventListener('connect', (event: Event) => {
            console.log('Notification SSE connected:', (event as MessageEvent).data);
        });

        eventSource.addEventListener('heartbeat', () => {
        });

        eventSource.addEventListener('notification-created', async (event: Event) => {
            try {
                console.log('실시간 알림 수신:', (event as MessageEvent).data);

                await Promise.all([
                    useNotificationStore.getState().fetchUnreadCount(),
                    useNotificationStore.getState().fetchNotifications(),
                ]);
            } catch (error) {
                console.error('Failed to refresh notifications after SSE event:', error);
            }
        });

        eventSource.addEventListener('error', () => {
            console.warn('Notification SSE reconnecting...');
        });

        return () => {
            console.info('Cleaning up Notification SSE connection');
            eventSource.close();
        };
    }, [enabled]);
};