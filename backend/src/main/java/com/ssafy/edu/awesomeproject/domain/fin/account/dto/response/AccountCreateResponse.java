package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import lombok.Builder;

/** 계좌 개설 직후 최소 정보만 반환하기 위한 DTO */
@Builder
public record AccountCreateResponse(String accountNo, String bankCode, String bankName) {}
