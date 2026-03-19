package com.ssafy.edu.awesomeproject.domain.community.dto.response;

public record ToggleReactionResponseDto(
        String targetType,
        Long targetId,
        String reactionType,
        Boolean active,
        Integer likeCount,
        Integer dislikeCount) {}
