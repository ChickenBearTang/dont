package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.Size;

/** 세이브박스 개설 요청. 계좌 별칭은 비워도 된다 (비우면 "세이브박스"). */
public record SaveBoxCreateRequest(@Size(max = 100) String accountName) {}
