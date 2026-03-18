package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record DeleteCommentResponseDto(Boolean deleted, LocalDateTime deletedAt) {}
