package com.ssafy.edu.awesomeproject.common.security.jwt;

import java.time.Instant;
import java.util.Map;

public record ParsedToken(
        String subject,
        String tokenId,
        TokenType tokenType,
        String sessionId,
        Instant expiresAt,
        Map<String, Object> claims) {}
