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
import com.ssafy.edu.awesomeproject.domain.notification.sse.NotificationSseEmitters;
import com.ssafy.edu.awesomeproject.domain.notification.sse.NotificationSsePayload;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

@Slf4j
@Service
@Transactional
public class NotificationService {
    private final NotificationRepository notificationRepository;
    private final UserRepository userRepository;
    private final CommentRepository commentRepository;
    private final NotificationSseEmitters notificationSseEmitters;

    public NotificationService(
        NotificationRepository notificationRepository,
        UserRepository userRepository,
        CommentRepository commentRepository,
        NotificationSseEmitters notificationSseEmitters) {
        this.notificationRepository = notificationRepository;
        this.userRepository = userRepository;
        this.commentRepository = commentRepository;
        this.notificationSseEmitters = notificationSseEmitters;
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
        log.info("알림 읽음 처리 시작 - userId={}, notificationId={}", userId, notificationId);

        validateUserExists(userId);

        Notification notification =
            notificationRepository
                .findByIdAndUserId(notificationId, userId)
                .orElseThrow(
                    () ->
                        new NotificationException(
                            NotificationErrorCode.NOTIFICATION_NOT_FOUND));

        notification.markAsRead();

        log.info("알림 읽음 처리 완료 - userId={}, notificationId={}", userId, notificationId);

        return new NotificationReadResponseDto(notification.getId(), notification.isRead());
    }

    public NotificationReadAllResponseDto markAllAsRead(Long userId) {
        log.info("알림 전체 읽음 처리 시작 - userId={}", userId);

        validateUserExists(userId);

        int updatedCount = notificationRepository.markAllAsRead(userId);

        log.info("알림 전체 읽음 처리 완료 - userId={}, updatedCount={}", userId, updatedCount);

        return new NotificationReadAllResponseDto(updatedCount);
    }

    public void createNotification(
        Long userId,
        NotificationType notificationType,
        String title,
        String body,
        NotificationReferenceType referenceType,
        Long referenceId) {
        log.info(
            "알림 생성 시작 - userId={}, type={}, title={}, referenceType={}, referenceId={}",
            userId,
            notificationType,
            title,
            referenceType,
            referenceId);

        validateUserExists(userId);

        if (title == null || title.isBlank() || body == null || body.isBlank()) {
            throw new NotificationException(NotificationErrorCode.INVALID_NOTIFICATION_REQUEST);
        }

        Notification notification =
            new Notification(userId, notificationType, title, body, referenceType, referenceId);

        Notification savedNotification = notificationRepository.save(notification);

        log.info(
            "알림 저장 완료 - notificationId={}, userId={}, type={}",
            savedNotification.getId(),
            userId,
            savedNotification.getNotificationType());

        NotificationSsePayload payload =
            new NotificationSsePayload(
                savedNotification.getId(),
                savedNotification.getNotificationType().name(),
                savedNotification.getTitle(),
                savedNotification.getBody(),
                savedNotification.getReferenceType() == null
                    ? null
                    : savedNotification.getReferenceType().name(),
                savedNotification.getReferenceId(),
                savedNotification.getPushedAt());


        if (TransactionSynchronizationManager.isActualTransactionActive()) {
            TransactionSynchronizationManager.registerSynchronization(
                new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        log.info(
                            "알림 SSE 발송(afterCommit) - notificationId={}, userId={}",
                            savedNotification.getId(),
                            userId);
                        notificationSseEmitters.sendToUser(userId, payload);
                    }
                });
        } else {
            log.info("알림 SSE 즉시 발송 - notificationId={}, userId={}", savedNotification.getId(), userId);
            notificationSseEmitters.sendToUser(userId, payload);
        }
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
                .orElseGet(
                    () -> {
                        log.warn(
                            "댓글 알림 대상 댓글을 찾지 못함 - notificationId={}, referenceId={}",
                            notification.getId(),
                            notification.getReferenceId());
                        return new NotificationTarget(null, notification.getReferenceId());
                    });
        }

        if (notification.getReferenceType() == NotificationReferenceType.POST
            && notification.getReferenceId() != null) {
            return new NotificationTarget(notification.getReferenceId(), null);
        }

        return new NotificationTarget(null, null);
    }

    private void validateUserExists(Long userId) {
        if (userId == null || !userRepository.existsById(userId)) {
            log.warn("존재하지 않는 사용자 알림 요청 - userId={}", userId);
            throw new NotificationException(NotificationErrorCode.USER_NOT_FOUND);
        }
    }

    private record NotificationTarget(Long postId, Long commentId) {}
}
