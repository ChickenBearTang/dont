package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record PrDetailResponseDto(
        Long postId,
        String title,
        Long authorId,
        String authorNickname,
        String authorProfileImageUrl,
        String itemName,
        Long priceAmount,
        String category,
        String content,
        String purchaseUrl,
        LocalDateTime deadlineAt,
        String status,
        String resultStatus,
        List<PostAttachmentResponseDto> attachments,
        LocalDateTime createdAt,
        LocalDateTime updatedAt,
        Long agreeCount,
        Long disagreeCount,
        Long totalVoteCount,
        LocalDateTime closedAt,
        List<PrDetailReviewDto> reviews,
        List<PrDetailEventDto> events,
        PrDetailPermissionsDto permissions) {}
