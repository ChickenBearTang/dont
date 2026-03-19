package com.ssafy.edu.awesomeproject.common.s3.dto.response;

import java.time.Instant;
import java.util.Map;

public record PresignedUrlResponse(
        String url, String method, Map<String, String> headers, String key, Instant expiresAt) {}
