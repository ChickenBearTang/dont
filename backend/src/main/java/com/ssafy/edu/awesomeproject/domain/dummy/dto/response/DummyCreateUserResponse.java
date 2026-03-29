package com.ssafy.edu.awesomeproject.domain.dummy.dto.response;

public record DummyCreateUserResponse(
        Long userId,
        Integer generationNo,
        Integer sequence,
        String email,
        String name,
        String nickname,
        String ssafyFinanceUserKey) {}
