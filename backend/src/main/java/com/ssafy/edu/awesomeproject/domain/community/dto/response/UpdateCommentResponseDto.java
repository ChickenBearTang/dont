package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record UpdateCommentResponseDto(Long commentId, LocalDateTime updatedAt) {}
