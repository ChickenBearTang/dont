package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PrDetailReviewDto(
        Long reviewId,
        Long userId,
        String decision,
        String content,
        LocalDateTime createdAt) {}
