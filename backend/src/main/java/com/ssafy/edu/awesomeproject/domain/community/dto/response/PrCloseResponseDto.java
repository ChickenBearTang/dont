package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PrCloseResponseDto(
        Long postId,
        String status,
        String resultStatus,
        Long agreeCount,
        Long disagreeCount,
        Long totalVoteCount,
        LocalDateTime closedAt) {}
