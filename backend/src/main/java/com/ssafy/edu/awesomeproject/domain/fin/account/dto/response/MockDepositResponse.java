package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import java.math.BigDecimal;
import lombok.Builder;

@Builder
public record MockDepositResponse(
        String transactionUniqueNo,
        BigDecimal balanceAfter,
        boolean autoSavingsExecuted,
        BigDecimal autoSavingsAmount) {}
