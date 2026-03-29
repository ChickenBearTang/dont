package com.ssafy.edu.awesomeproject.domain.community.dto.request;

public record PrXaiFinanceProfileDto(
        PrXaiProvenanceValueDto currentBalance,
        PrXaiProvenanceValueDto emergencyFundBalance,
        PrXaiProvenanceValueDto saveboxBalance,
        PrXaiProvenanceValueDto expectedCardPaymentAmount,
        PrXaiProvenanceValueDto daysUntilCardDue) {}
