package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import lombok.Builder;

@Builder
public record AccountCreateResponse(String accountNo, String bankCode, String bankName) {}
