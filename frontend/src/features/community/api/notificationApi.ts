import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  NotificationListResponseDto,
  NotificationUnreadCountResponseDto,
} from '../types/notification';

export const getNotifications = async (
  page: number = 0,
  size: number = 20
): Promise<ApiResponse<NotificationListResponseDto>> => {
  return await axiosInstance.get('/notifications', {
    params: { page, size },
  });
};

export const getUnreadCount = async (): Promise<
  ApiResponse<NotificationUnreadCountResponseDto>
> => {
  return await axiosInstance.get('/notifications/unread-count');
};

export const markAsRead = async (notificationId: number): Promise<ApiResponse<void>> => {
  return await axiosInstance.patch(`/notifications/${notificationId}/read`);
};

export const markAllAsRead = async (): Promise<ApiResponse<void>> => {
  return await axiosInstance.patch('/notifications/read-all');
};
