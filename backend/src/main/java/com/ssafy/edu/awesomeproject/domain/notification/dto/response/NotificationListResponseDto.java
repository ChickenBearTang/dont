package com.ssafy.edu.awesomeproject.domain.notification.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record NotificationListResponseDto(
        List<NotificationSummaryDto> content,
        int page,
        int size,
        long totalElements,
        int totalPages,
        boolean hasNext) {

    public record NotificationSummaryDto(
            Long notificationId,
            String notificationType,
            String title,
            String body,
            String referenceType,
            Long referenceId,
            boolean isRead,
            LocalDateTime pushedAt,
            LocalDateTime createdAt,
            Long postId,
            Long commentId) {}
}
