package com.ssafy.edu.awesomeproject.domain.dummy.client.dto.response;

public record FinanceMemberSearchResponse(
        String userId,
        String userName,
        String institutionCode,
        String userKey,
        String created,
        String modified) {}
