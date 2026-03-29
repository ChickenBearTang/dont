package com.ssafy.edu.awesomeproject.domain.notification.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationListResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationReadAllResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationReadResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.dto.response.NotificationUnreadCountResponseDto;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/notifications")
public class NotificationController {

    private final NotificationService notificationService;

    public NotificationController(NotificationService notificationService) {
        this.notificationService = notificationService;
    }

    @GetMapping
    @ApiCommonResponses
    @Operation(summary = "알림 목록 조회 API", description = "현재 로그인한 사용자의 알림 목록을 조회합니다.")
    public CommonResponse<NotificationListResponseDto> getNotifications(
            @CurrentUserId Long userId,
            @RequestParam(required = false) Integer page,
            @RequestParam(required = false) Integer size) {
        return CommonResponse.success(notificationService.getNotifications(userId, page, size));
    }

    @GetMapping("/unread-count")
    @ApiCommonResponses
    @Operation(summary = "읽지 않은 알림 개수 조회 API", description = "현재 로그인한 사용자의 읽지 않은 알림 개수를 조회합니다.")
    public CommonResponse<NotificationUnreadCountResponseDto> getUnreadCount(
            @CurrentUserId Long userId) {
        return CommonResponse.success(notificationService.getUnreadCount(userId));
    }

    @PatchMapping("/{notificationId}/read")
    @ApiCommonResponses
    @Operation(summary = "알림 읽음 처리 API", description = "특정 알림을 읽음 처리합니다.")
    public CommonResponse<NotificationReadResponseDto> markAsRead(
            @CurrentUserId Long userId, @PathVariable Long notificationId) {
        return CommonResponse.success(notificationService.markAsRead(userId, notificationId));
    }

    @PatchMapping("/read-all")
    @ApiCommonResponses
    @Operation(summary = "전체 알림 읽음 처리 API", description = "현재 로그인한 사용자의 모든 알림을 읽음 처리합니다.")
    public CommonResponse<NotificationReadAllResponseDto> markAllAsRead(
            @CurrentUserId Long userId) {
        return CommonResponse.success(notificationService.markAllAsRead(userId));
    }
}
