package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import java.math.BigDecimal;
import lombok.Builder;

@Builder
public record SavingsSettingRequest(
        @NotNull Long primaryAccountId,
        @NotNull Long saveboxAccountId,
        @NotBlank String keyword,
        @NotNull @PositiveOrZero BigDecimal savingsAmount,
        boolean isActive) {}
