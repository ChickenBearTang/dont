package com.ssafy.edu.awesomeproject.domain.fin.account.dto.request;

import jakarta.validation.constraints.NotBlank;

/** 사용자가 세이브 박스를 개설할 때 보내는 요청 DTO (현재는 고유 번호 정도만 필요할 수 있음) */
public record SaveBoxCreateRequest(@NotBlank String accountTypeUniqueNo) {}
