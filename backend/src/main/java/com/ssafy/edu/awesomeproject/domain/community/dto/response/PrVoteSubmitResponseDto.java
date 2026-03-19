package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PrVoteSubmitResponseDto(
        Long postId, Long userId, String voteValue, String opinionText, LocalDateTime votedAt) {}
