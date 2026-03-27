package com.ssafy.edu.awesomeproject.domain.dummy.dto.response;

public record DummyCreateAccountsResponse(
        Long userId,
        String saveBoxAccountNo,
        Long saveBoxAccountId,
        String primaryAccountNo,
        Long primaryAccountId,
        Long savingsSettingId) {}
