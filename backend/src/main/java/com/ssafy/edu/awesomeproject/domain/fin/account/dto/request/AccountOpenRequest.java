package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.Size;

/** 입출금 계좌 개설 요청. 계좌 별칭은 비워도 된다 (비우면 "입출금 통장"). */
public record AccountOpenRequest(@Size(max = 100) String accountName) {}
