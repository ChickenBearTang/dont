package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import java.util.List;

public record PrXaiEvaluationRequestDto(
        String requestId,
        String schemaVersion,
        String contextVersion,
        PrXaiPurchaseContextDto purchase,
        PrXaiFinanceProfileDto financeProfile,
        List<PrXaiRecentTransactionDto> recentTransactions) {}
