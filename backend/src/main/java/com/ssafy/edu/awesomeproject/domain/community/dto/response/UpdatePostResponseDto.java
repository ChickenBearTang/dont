package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record UpdatePostResponseDto(Long postId, LocalDateTime updatedAt) {}
