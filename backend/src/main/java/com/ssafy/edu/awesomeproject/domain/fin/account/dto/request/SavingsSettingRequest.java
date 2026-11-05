package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import lombok.Builder;

@Builder
public record SavingsSettingRequest(
        @NotNull Long primaryAccountId,
        @NotNull Long saveboxAccountId,
        @NotBlank @Size(max = 100) String keyword,
        @NotNull @PositiveOrZero @Digits(integer = 13, fraction = 2, message = "금액이 너무 큽니다.") BigDecimal savingsAmount,
        boolean isActive) {}
