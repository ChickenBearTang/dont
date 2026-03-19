package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import java.math.BigDecimal;
import lombok.Builder;

@Builder
public record SavingsSettingResponse(
        Long id,
        Long primaryAccountId,
        Long saveboxAccountId,
        String keyword,
        BigDecimal savingsAmount,
        boolean isActive) {}
