package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record AdminReportDetailResponseDto(
        Long reportId,
        Long reporterUserId,
        String targetType,
        Long targetId,
        String reasonCode,
        String detailText,
        String reportStatus,
        Long processedByUserId,
        String processNote,
        LocalDateTime processedAt,
        LocalDateTime createdAt,
        LocalDateTime updatedAt,
        String targetAuthorNickname,
        String targetTitle,
        String targetContent,
        String targetStatus,
        Long postId) {}
