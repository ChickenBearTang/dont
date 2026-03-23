package com.ssafy.edu.awesomeproject.domain.user.dto.request;

import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public record MyPageUpdateRequestDto(
        @Size(max = 50) String name,
        @Past LocalDate birthDate,
        @PositiveOrZero Long monthlySavingGoalAmount) {}
