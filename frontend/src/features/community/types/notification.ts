export type NotificationType =
  | 'POST_COMMENT_CREATED'
  | 'POST_REPORTED'
  | 'COMMENT_REPORTED'
  | 'REPORT_PROCESSED_BLINDED'
  | 'REPORT_PROCESSED_REJECTED'
  | 'POST_BLINDED'
  | 'COMMENT_BLINDED'
  | 'MANUAL_SAVINGS_COMPLETED'
  | 'AUTO_SAVINGS_COMPLETED'
  | 'FINANCE_GENERIC'
  | 'CONSUMPTION_REPORT_READY'
  | string;

export type NotificationReferenceType = 'POST' | 'COMMENT' | 'FINANCE' | string;

export interface NotificationSummaryDto {
  notificationId: number;
  notificationType: NotificationType;
  title: string;
  body: string;
  referenceType: NotificationReferenceType;
  referenceId: number;
  isRead: boolean;
  pushedAt: string;
  createdAt: string;
  postId?: number | null;
  commentId?: number | null;
}

export interface NotificationListResponseDto {
  content: NotificationSummaryDto[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
}

export interface NotificationUnreadCountResponseDto {
  unreadCount: number;
}