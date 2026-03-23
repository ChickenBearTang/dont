package com.ssafy.edu.awesomeproject.domain.user.dto.response;

import java.time.LocalDate;

public record MyPageResponseDto(
        Long userId,
        String email,
        String name,
        String nickname,
        LocalDate birthDate,
        String profileImageUrl,
        String onboardingStatus,
        Long monthlySavingGoalAmount,
        Long cohortId,
        Integer cohortGenerationNo) {}
