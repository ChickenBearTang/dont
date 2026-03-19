package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PollVoteSubmitResponseDto(
        Long postId,
        Long userId,
        String voteOption,
        Long optionACount,
        Long optionBCount,
        Long totalVoteCount,
        LocalDateTime updatedAt) {}
