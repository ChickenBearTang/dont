package com.ssafy.edu.awesomeproject.domain.auth.dto.response;

public record EmailVerificationConfirmResponseDto(
        String email, boolean verified, long verifiedExpiresInSeconds) {}
