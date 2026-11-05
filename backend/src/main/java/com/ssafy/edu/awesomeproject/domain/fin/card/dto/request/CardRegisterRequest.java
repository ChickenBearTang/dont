package com.ssafy.edu.awesomeproject.domain.fin.card.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** 카드 등록 요청 (개발·시연용). 결제일은 매월 며칠인지(1~28)이며, 비우면 1일이다. */
public record CardRegisterRequest(
        @NotBlank @Size(max = 128) String cardIssuerName,
        @NotBlank @Size(max = 128) String cardName,
        @Pattern(regexp = "^([1-9]|1\\d|2[0-8])$", message = "결제일은 1~28 사이의 날짜여야 합니다.")
                String withdrawalDate) {}
