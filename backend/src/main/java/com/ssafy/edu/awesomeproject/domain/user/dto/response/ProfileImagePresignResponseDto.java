package com.ssafy.edu.awesomeproject.domain.user.dto.response;

import java.time.Instant;
import java.util.Map;

public record ProfileImagePresignResponseDto(
        String uploadUrl,
        String method,
        Map<String, String> headers,
        String key,
        Instant expiresAt,
        String publicUrl) {}
