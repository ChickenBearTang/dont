package com.ssafy.edu.awesomeproject.domain.auth.dto.response;

public record LoginResponseDto(
        Long userId,
        String email,
        String userRole,
        String accessToken,
        String tokenType,
        long expiresInSeconds) {}
