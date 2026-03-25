package com.ssafy.edu.awesomeproject.domain.community.dto.request;

public record PrXaiRecentTransactionDto(
        String transactionDate,
        String transactionTime,
        String merchantName,
        String categoryName,
        int transactionAmount) {}
