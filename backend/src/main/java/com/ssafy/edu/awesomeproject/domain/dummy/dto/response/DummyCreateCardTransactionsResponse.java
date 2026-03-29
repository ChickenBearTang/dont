package com.ssafy.edu.awesomeproject.domain.dummy.dto.response;

public record DummyCreateCardTransactionsResponse(
        Long userId,
        Long cardId,
        String startDate,
        String endDate,
        int insertedCount,
        long totalAmount) {}
