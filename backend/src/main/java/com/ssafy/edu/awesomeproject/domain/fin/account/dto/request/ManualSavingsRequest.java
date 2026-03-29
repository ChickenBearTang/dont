package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record ManualSavingsRequest(
        @NotNull(message = "저축 금액은 필수입니다.")
        @DecimalMin(value = "0.0", inclusive = false, message = "저축 금액은 0원보다 커야 합니다.")
        BigDecimal amount,

        @NotBlank(message = "비밀번호 확인이 필요합니다.")
        String password
) {}
