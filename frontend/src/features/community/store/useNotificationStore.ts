import { create } from 'zustand';
import * as notificationApi from '../api/notificationApi';
import type { NotificationSummaryDto } from '../types/notification';

interface NotificationState {
  notifications: NotificationSummaryDto[];
  unreadCount: number;
  loading: boolean;
  pollingInterval: number | null;
  dismissedIds: Set<number>;

  fetchNotifications: () => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: (notificationId: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  dismissNotification: (notificationId: number) => Promise<void>;
  startPolling: (intervalMs?: number) => void;
  stopPolling: () => void;
}

const STORAGE_KEY = 'dismissed_notifications';

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,
  pollingInterval: null,
  dismissedIds: new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')),

  fetchNotifications: async () => {
    set({ loading: true });
    try {
      const res = await notificationApi.getNotifications(0, 30);
      if (res.data) {
        const { dismissedIds } = get();
        const filtered = res.data.content.filter((n) => !dismissedIds.has(n.notificationId));
        set({ notifications: filtered.slice(0, 10) });
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      set({ loading: false });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const prevUnreadCount = get().unreadCount;
      const res = await notificationApi.getUnreadCount();

      if (res.data) {
        const nextUnreadCount = res.data.unreadCount;
        set({ unreadCount: nextUnreadCount });


        if (nextUnreadCount > prevUnreadCount) {
          await get().fetchNotifications();
        }
      }
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  },

  markAsRead: async (notificationId: number) => {
    const target = get().notifications.find((n) => n.notificationId === notificationId);
    if (!target || target.isRead) {
      return;
    }

    try {
      await notificationApi.markAsRead(notificationId);
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.notificationId === notificationId ? { ...n, isRead: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  },

  markAllAsRead: async () => {
    try {
      await notificationApi.markAllAsRead();
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, isRead: true })),
        unreadCount: 0,
      }));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  },

  dismissNotification: async (notificationId: number) => {
    const target = get().notifications.find((n) => n.notificationId === notificationId);
    if (!target) {
      return;
    }

    try {
      if (!target.isRead) {
        await notificationApi.markAsRead(notificationId);
      }

      set((state) => {
        const nextDismissed = new Set(state.dismissedIds).add(notificationId);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(nextDismissed)));

        return {
          dismissedIds: nextDismissed,
          notifications: state.notifications.filter((n) => n.notificationId !== notificationId),
          unreadCount: target.isRead ? state.unreadCount : Math.max(0, state.unreadCount - 1),
        };
      });
    } catch (error) {
      console.error('Failed to dismiss notification:', error);
    }
  },

  startPolling: (intervalMs = 30000) => {
    const { pollingInterval } = get();
    if (pollingInterval) return;

    get().fetchUnreadCount();
    get().fetchNotifications();

    const interval = window.setInterval(() => {
      get().fetchUnreadCount();
    }, intervalMs);

    set({ pollingInterval: interval });
  },

  stopPolling: () => {
    const { pollingInterval } = get();
    if (pollingInterval) {
      window.clearInterval(pollingInterval);
      set({ pollingInterval: null });
    }
  },
}));