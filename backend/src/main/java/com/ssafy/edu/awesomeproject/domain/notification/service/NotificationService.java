package com.ssafy.edu.awesomeproject.domain.notification.service;

import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.CommentRepository;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationListResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationReadAllResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationReadResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationUnreadCountResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.entity.Notification;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.error.NotificationErrorCode;
import com.ssafy.edu.awesomeproject.domain.notification.error.NotificationException;
import com.ssafy.edu.awesomeproject.domain.notification.repository.NotificationRepository;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class NotificationService {
    private final NotificationRepository notificationRepository;
    private final UserRepository userRepository;
    private final CommentRepository commentRepository;

    public NotificationService(
            NotificationRepository notificationRepository,
            UserRepository userRepository,
            CommentRepository commentRepository) {
        this.notificationRepository = notificationRepository;
        this.userRepository = userRepository;
        this.commentRepository = commentRepository;
    }

    @Transactional(readOnly = true)
    public NotificationListResponseDto getNotifications(Long userId, Integer page, Integer size) {
        validateUserExists(userId);

        int pageNumber = (page == null || page < 0) ? 0 : page;
        int pageSize = (size == null || size <= 0) ? 20 : size;

        PageRequest pageRequest =
                PageRequest.of(pageNumber, pageSize, Sort.by(Sort.Direction.DESC, "id"));

        Page<Notification> notificationPage =
                notificationRepository.findByUserIdOrderByIdDesc(userId, pageRequest);

        List<NotificationListResponseDto.NotificationSummaryDto> content =
            notificationPage.getContent().stream()
                .map(
                    notification -> {
                        NotificationTarget target = resolveTarget(notification);

                        return new NotificationListResponseDto.NotificationSummaryDto(
                            notification.getId(),
                            notification.getNotificationType().name(),
                            notification.getTitle(),
                            notification.getBody(),
                            notification.getReferenceType() == null
                                ? null
                                : notification.getReferenceType().name(),
                            notification.getReferenceId(),
                            notification.isRead(),
                            notification.getPushedAt(),
                            notification.getCreatedAt(),
                            target.postId(),
                            target.commentId());
                    })
                .toList();

        return new NotificationListResponseDto(
                content,
                notificationPage.getNumber(),
                notificationPage.getSize(),
                notificationPage.getTotalElements(),
                notificationPage.getTotalPages(),
                notificationPage.hasNext());
    }

    @Transactional(readOnly = true)
    public NotificationUnreadCountResponseDto getUnreadCount(Long userId) {
        validateUserExists(userId);

        long unreadCount = notificationRepository.countByUserIdAndIsReadFalse(userId);
        return new NotificationUnreadCountResponseDto(unreadCount);
    }

    public NotificationReadResponseDto markAsRead(Long userId, Long notificationId) {
        validateUserExists(userId);

        Notification notification =
                notificationRepository
                        .findByIdAndUserId(notificationId, userId)
                        .orElseThrow(
                            () ->
                                    new NotificationException(
                                            NotificationErrorCode.NOTIFICATION_NOT_FOUND));

        notification.markAsRead();

        return new NotificationReadResponseDto(notification.getId(), notification.isRead());
    }

    public NotificationReadAllResponseDto markAllAsRead(Long userId) {
        validateUserExists(userId);
        int updatedCount = notificationRepository.markAllAsRead(userId);
        return new NotificationReadAllResponseDto(updatedCount);
    }

    public void createNotification(
            Long userId,
            NotificationType notificationType,
            String title,
            String body,
            NotificationReferenceType referenceType,
            Long referenceId) {
        validateUserExists(userId);

        if (title == null || title.isBlank() || body == null || body.isBlank()) {
            throw new NotificationException(NotificationErrorCode.INVALID_NOTIFICATION_REQUEST);
        }

        Notification notification =
                new Notification(userId, notificationType, title, body, referenceType, referenceId);

        notificationRepository.save(notification);
    }

    private NotificationTarget resolveTarget(Notification notification) {
        if (notification.getReferenceType() == NotificationReferenceType.COMMENT
            && notification.getReferenceId() != null) {
            return commentRepository
                .findById(notification.getReferenceId())
                .map(
                    comment ->
                        new NotificationTarget(
                            comment.getPost().getId(), comment.getId()))
                .orElseGet(() -> new NotificationTarget(null, notification.getReferenceId()));
        }

        if (notification.getReferenceType() == NotificationReferenceType.POST
            && notification.getReferenceId() != null) {
            return new NotificationTarget(notification.getReferenceId(), null);
        }

        return new NotificationTarget(null, null);
    }

    private void validateUserExists(Long userId) {
        if (userId == null || !userRepository.existsById(userId)) {
            throw new NotificationException(NotificationErrorCode.USER_NOT_FOUND);
        }
    }

    private record NotificationTarget(Long postId, Long commentId) {}
}
