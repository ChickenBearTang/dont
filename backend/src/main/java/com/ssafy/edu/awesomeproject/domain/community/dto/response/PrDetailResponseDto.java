package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PrDetailResponseDto(
        Long postId,
        String itemName,
        Long priceAmount,
        String category,
        String content,
        String purchaseUrl,
        String imageUrl,
        String status,
        String resultStatus,
        Long agreeCount,
        Long disagreeCount,
        Long totalVoteCount,
        LocalDateTime closedAt) {}
