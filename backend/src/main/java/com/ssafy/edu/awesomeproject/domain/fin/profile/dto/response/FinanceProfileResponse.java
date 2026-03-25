package com.ssafy.edu.awesomeproject.domain.fin.profile.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

public record FinanceProfileResponse(
        @JsonProperty("current_balance") double currentBalance,
        @JsonProperty("emergency_fund_balance") double emergencyFundBalance,
        @JsonProperty("expected_card_payment_amount") double expectedCardPaymentAmount,
        @JsonProperty("days_until_card_due") int daysUntilCardDue) {}
