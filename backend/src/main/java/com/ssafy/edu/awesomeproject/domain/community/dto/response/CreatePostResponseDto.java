package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record CreatePostResponseDto (
    Long postId,
    String category,
    LocalDateTime createdAt
) {}
