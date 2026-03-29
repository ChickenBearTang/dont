package com.ssafy.edu.awesomeproject.domain.dummy.dto.response;

public record DummyCreateAllResponse(
        Integer generationNo,
        DummyCreateUserResponse user,
        DummyCreateAccountsResponse accounts,
        DummyCreateCardResponse card,
        DummyCreateCardTransactionsResponse cardTransactions) {}
