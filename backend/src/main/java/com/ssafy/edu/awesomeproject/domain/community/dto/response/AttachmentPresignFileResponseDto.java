package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.Instant;
import java.util.Map;

public record AttachmentPresignFileResponseDto(
        String uploadUrl,
        String method,
        Map<String, String> headers,
        String key,
        Instant expiresAt,
        String fileUrl) {}
