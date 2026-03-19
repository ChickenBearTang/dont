package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PrCreateResponseDto(Long postId, String resultStatus, LocalDateTime deadlineAt) {}
