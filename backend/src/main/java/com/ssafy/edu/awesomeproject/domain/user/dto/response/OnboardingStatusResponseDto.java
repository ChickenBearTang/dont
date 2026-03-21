package com.ssafy.edu.awesomeproject.domain.user.dto.response;

public record OnboardingStatusResponseDto(
        String onboardingStatus, boolean onboardingCompleted, Long recommendedAmount) {}
