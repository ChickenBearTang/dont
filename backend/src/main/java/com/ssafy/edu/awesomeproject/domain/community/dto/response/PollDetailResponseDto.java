package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PollDetailResponseDto(
        Long postId,
        String title,
        String content,
        String authorNickname,
        String question,
        String optionA,
        String optionB,
        LocalDateTime deadlineAt,
        Boolean isClosed,
        Long optionACount,
        Long optionBCount,
        Long totalVoteCount,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}
