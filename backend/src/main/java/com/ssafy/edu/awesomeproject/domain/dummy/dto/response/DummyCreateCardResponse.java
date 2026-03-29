package com.ssafy.edu.awesomeproject.domain.dummy.dto.response;

public record DummyCreateCardResponse(
        Long userId,
        String cardUniqueNo,
        String withdrawalAccountNo,
        int refreshedCardCount) {}
