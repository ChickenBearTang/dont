package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PollUpdateResponseDto(Long postId, LocalDateTime updatedAt) {}
