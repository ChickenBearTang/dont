package com.ssafy.edu.awesomeproject.domain.auth.dto.response;

public record PasswordResetRequestResponseDto(String message, long expiresInSeconds) {}
