package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import java.math.BigDecimal;
import lombok.Builder;

@Builder
public record SavingsSettingRequest(
        Long primaryAccountId,
        Long saveboxAccountId,
        String keyword,
        BigDecimal savingsAmount,
        boolean isActive) {}
