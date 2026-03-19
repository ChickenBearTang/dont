package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record HotdealDetailResponseDto(
        Long postId,
        String title,
        String content,
        String authorNickname,
        String productName,
        String storeName,
        Long dealPriceAmount,
        Long originalPriceAmount,
        String dealUrl,
        String shippingInfo,
        LocalDateTime expiredAt,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}
