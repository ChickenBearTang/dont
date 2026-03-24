package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record HotdealDetailResponseDto(
        Long postId,
        String title,
        String content,
        Long authorId,
        String authorNickname,
        String authorProfileImageUrl,
        String productName,
        String storeName,
        Long dealPriceAmount,
        Long originalPriceAmount,
        String dealUrl,
        String shippingInfo,
        LocalDateTime expiredAt,
        List<PostAttachmentResponseDto> attachments,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}
