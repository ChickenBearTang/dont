package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record DeletePostResponseDto(boolean deleted, LocalDateTime deletedAt) {}
