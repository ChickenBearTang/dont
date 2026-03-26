package com.ssafy.edu.awesomeproject.domain.notification.sse;

import java.time.LocalDateTime;

public record NotificationSsePayload (
        Long notificationId,
        String notificationType,
        String title,
        String body,
        String referenceType,
        Long referenceId,
        LocalDateTime pushedAt) {}
