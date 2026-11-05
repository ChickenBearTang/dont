package com.ssafy.edu.awesomeproject.domain.fin.card.dto.request;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

/** 카드 결제내역 입력 요청 (개발·시연용). 결제일을 비우면 오늘이다 (yyyyMMdd 또는 yyyy-MM-dd). */
public record MockCardTransactionRequest(
        @NotBlank @Size(max = 255) String merchantName,
        @Size(max = 128) String categoryName,
        @NotNull @Positive @Max(100_000_000L) Long amount,
        @Size(max = 10) String transactionDate) {}
