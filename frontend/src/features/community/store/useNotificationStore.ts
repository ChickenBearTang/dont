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
  dismissNotification: (notificationId: number) => void;
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
      // - [x] Backend: Restore stable versions of `CommentService`, `ReportService`, `NotificationController`, `CommentController` (Fixed 500 errors)
      // - [x] Frontend: Implement notification dismissal UI ('X' button in Header)
      // - [x] Frontend: Implement notification dismissal logic (Local storage fallback)
      // - [x] Frontend: Improve notification navigation to posts
      // - [ ] Frontend: (Optional) Highlight target comments (Restricted by current backend state)
      const res = await notificationApi.getNotifications(0, 30); // Get more to account for dismissals
      if (res.data) {
        const { dismissedIds } = get();
        const filtered = res.data.content.filter((n) => !dismissedIds.has(n.notificationId));
        set({ notifications: filtered.slice(0, 10) }); // Keep only top 10
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      set({ loading: false });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const res = await notificationApi.getUnreadCount();
      if (res.data) {
        set({ unreadCount: res.data.unreadCount });
      }
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  },

  markAsRead: async (notificationId: number) => {
    try {
      await notificationApi.markAsRead(notificationId);
      // Optimistic update
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

  dismissNotification: (notificationId: number) => {
    set((state) => {
      const nextDismissed = new Set(state.dismissedIds).add(notificationId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(nextDismissed)));
      return {
        dismissedIds: nextDismissed,
        notifications: state.notifications.filter((n) => n.notificationId !== notificationId),
      };
    });
  },

  startPolling: (intervalMs = 30000) => {
    const { pollingInterval } = get();
    if (pollingInterval) return;

    // Initial fetch
    get().fetchUnreadCount();

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
