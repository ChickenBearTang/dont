package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * AI 서버로 보내는 재무 프로필. 모든 값에 출처(provenance)를 붙인다.
 *
 * <p>월 소득/고정지출은 DB 에 열이 없어서 계좌 거래에서 추정한 값(isEstimated)이다. 추정할 근거가 없으면 null 이고,
 * 이때는 필드를 아예 보내지 않는다 (기본값으로 채우지 않는다 — AI 가 5·3·2 예산 규칙을 "판단 불가"로 둔다).
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record PrXaiFinanceProfileDto(
        PrXaiProvenanceValueDto currentBalance,
        PrXaiProvenanceValueDto emergencyFundBalance,
        PrXaiProvenanceValueDto saveboxBalance,
        PrXaiProvenanceValueDto expectedCardPaymentAmount,
        PrXaiProvenanceValueDto daysUntilCardDue,
        PrXaiProvenanceValueDto availableFixedIncome,
        PrXaiProvenanceValueDto availableFixedExpense) {}
