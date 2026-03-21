package com.ssafy.edu.awesomeproject.domain.user.dto.request;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

public record OnboardingCheckpointRequestDto(@NotNull @PositiveOrZero Long recommendedAmount) {}
