package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record PrDetailResponseDto(
        Long postId,
        String title,
        Long authorId,
        String authorNickname,
        String itemName,
        Long priceAmount,
        String category,
        String content,
        String purchaseUrl,
        String imageUrl,
        LocalDateTime deadlineAt,
        String status,
        String resultStatus,
        LocalDateTime createdAt,
        LocalDateTime updatedAt,
        Long agreeCount,
        Long disagreeCount,
        Long totalVoteCount,
        LocalDateTime closedAt,
        List<PrDetailReviewDto> reviews,
        List<PrDetailEventDto> events,
        PrDetailPermissionsDto permissions) {}
