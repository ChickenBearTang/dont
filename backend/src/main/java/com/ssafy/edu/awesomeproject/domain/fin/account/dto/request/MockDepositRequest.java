package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/** 모의 입금 요청 (개발·시연용). 적요에 자동저축 키워드를 넣으면 자동저축이 바로 돈다. */
public record MockDepositRequest(
        @NotNull(message = "입금 금액은 필수입니다.")
        @DecimalMin(value = "0.0", inclusive = false, message = "입금 금액은 0원보다 커야 합니다.")
        @Digits(integer = 13, fraction = 2, message = "금액이 너무 큽니다.")
        BigDecimal amount,

        @Size(max = 200) String summary,

        @Size(max = 500) String memo) {}
