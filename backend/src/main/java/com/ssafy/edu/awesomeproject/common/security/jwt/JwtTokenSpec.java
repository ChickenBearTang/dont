package com.ssafy.edu.awesomeproject.common.security.jwt;

import java.util.Map;

public record JwtTokenSpec(
        String subject,
        String tokenId,
        TokenType tokenType,
        String sessionId,
        Map<String, Object> claims,
        long ttlSeconds) {
    public static JwtTokenSpec access(
            String subject, String tokenId, Map<String, Object> claims, long ttlSeconds) {
        return new JwtTokenSpec(subject, tokenId, TokenType.ACCESS, null, claims, ttlSeconds);
    }

    public static JwtTokenSpec refresh(
            String subject,
            String tokenId,
            String sessionId,
            Map<String, Object> claims,
            long ttlSeconds) {
        return new JwtTokenSpec(subject, tokenId, TokenType.REFRESH, sessionId, claims, ttlSeconds);
    }
}
