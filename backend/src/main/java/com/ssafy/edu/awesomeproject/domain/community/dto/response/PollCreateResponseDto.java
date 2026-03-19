package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PollCreateResponseDto(Long postId, LocalDateTime createdAt) {}
