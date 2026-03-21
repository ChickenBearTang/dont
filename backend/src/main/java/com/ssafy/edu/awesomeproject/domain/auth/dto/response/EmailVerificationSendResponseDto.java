package com.ssafy.edu.awesomeproject.domain.auth.dto.response;

public record EmailVerificationSendResponseDto(String email, long expiresInSeconds) {}
