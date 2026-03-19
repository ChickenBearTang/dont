package com.ssafy.edu.awesomeproject.domain.auth.dto.response;

public record TokenReissueResponseDto(
        String accessToken, String tokenType, long expiresInSeconds) {}
