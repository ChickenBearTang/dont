package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiFinanceProfileDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiProvenanceValueDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvidenceDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiSectionDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiTopFactorDto;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import lombok.extern.slf4j.Slf4j;

/**
 * 구매 PR 작성자가 아닌 사용자에게 XAI 평가를 보여줄 때 작성자의 재무 정보를 가린다.
 *
 * <p>XAI 평가는 PR 작성자의 잔액·소득·지출로 계산한다. 투표하는 사람에게는 판정과 이유, 가격 평가가 필요하지만 작성자의
 * 금액까지 보일 이유는 없다. 응답에는 금액이 여러 곳에 들어 있다: 재무 지표 값, 근거 값, 반사실 문구, 요약 문장 끝의 제안.
 *
 * <p>금액만 지우는 방식으로는 부족하다. 생활비 구역 사용률(예: 84% → 103%)은 금액이 아니지만 공개된 상품 가격과 함께
 * 보면 한도(가격 ÷ 사용률 증가분)와 소득(한도 × 2)을 거꾸로 계산할 수 있다. 요인의 영향도도 같은 사용률에서 바로
 * 계산된다. 그래서 허용 목록으로 가격 쪽 항목만 남기고, 재무 쪽은 숫자 없는 이유 문장과 상태만 남긴다. 허용 목록에 없는
 * 것은 모두 나가지 않는다 (AI 응답에 새 필드가 생겨도 기본이 "숨김"이다).
 *
 * <p>마지막 방어선으로, 남긴 문장에 작성자의 실제 금액이 그대로 들어 있으면 그 문장을 가린다 (AI 문구가 바뀌어 금액이
 * 섞이는 경우).
 */
@Slf4j
final class PrXaiEvaluationRedactor {

    /** 상품 가격 정보만 담은 요인. 영향도까지 그대로 보여 준다. */
    private static final Set<String> PRICE_FACTOR_CODES =
            Set.of(
                    "PRICE_RELATIVE_TO_30D_AVG",
                    "CURRENT_PRICE_LEVEL",
                    "COUPON_DISCOUNT_APPLIED",
                    "SHIPPING_COST_REDUCES_ATTRACTIVENESS",
                    "PRICE_MODEL_GAP_SIGNAL",
                    "PRICE_ONLY_FALLBACK");

    private static final Set<String> PRICE_EVIDENCE_FIELDS =
            Set.of("current_price", "avg_price_30d", "coupon_applied", "shipping_fee", "price_model_gap_score");

    /** 가격·수집 관련 경고만. 재무 입력 경고(추정, 예산 판단 불가, 비상금 부족)는 작성자의 사정을 말해 주므로 뺀다. */
    private static final Set<String> PUBLIC_WARNINGS =
            Set.of(
                    "CRAWL_FETCH_FAILED",
                    "PRICE_ESTIMATED_FROM_REQUEST",
                    "NO_PRICE_HISTORY",
                    "PRICE_HISTORY_READ_FAILED",
                    "MISSING_PURCHASE_URL",
                    "ITEM_FAMILY_UNCLASSIFIED",
                    "PRICE_MODEL_UNTRUSTED",
                    "CRAWLED_PRICE_DIVERGES_FROM_REQUEST");

    /** AI 서버의 요약 첫 문장(xai/polisher.py)과 같은 문구. 요약을 AI 텍스트에서 자르지 않고 판정으로 다시 만든다. */
    private static final Map<String, String> LEAD =
            Map.of(
                    "BUY_NOW", "지금 구매해도 좋은 조건입니다.",
                    "WAIT", "조금 더 지켜보는 것을 권합니다.",
                    "NOT_RECOMMENDED", "지금은 구매를 권하지 않습니다.");

    private static final String DEFAULT_LEAD = "구매 전에 한 번 더 검토해 보세요.";
    private static final String HIDDEN_TEXT = "재무 상황에 대한 자세한 내용은 작성자에게만 보여요.";

    /** 12일, 30일 같은 작은 수를 금액으로 착각하지 않도록 1000원 이상만 대조한다. */
    private static final long MIN_SENSITIVE_AMOUNT = 1_000L;

    private PrXaiEvaluationRedactor() {}

    /** AI 에 보낸 재무 프로필에서 작성자의 금액(원)을 모은다. 마지막 방어선이 이 값으로 문장을 대조한다. */
    static List<Long> sensitiveAmounts(PrXaiFinanceProfileDto profile) {
        if (profile == null) {
            return List.of();
        }
        List<Long> amounts = new ArrayList<>();
        for (PrXaiProvenanceValueDto provenance :
                Arrays.asList(
                        profile.currentBalance(),
                        profile.emergencyFundBalance(),
                        profile.saveboxBalance(),
                        profile.expectedCardPaymentAmount(),
                        profile.availableFixedIncome(),
                        profile.availableFixedExpense(),
                        profile.monthlySpending30d())) {
            if (provenance != null && provenance.value() instanceof Number number) {
                long amount = Math.abs(Math.round(number.doubleValue()));
                if (amount >= MIN_SENSITIVE_AMOUNT && !amounts.contains(amount)) {
                    amounts.add(amount);
                }
            }
        }
        return List.copyOf(amounts);
    }

    /** 작성자가 아닌 사용자에게 내려 줄 응답. 원본은 건드리지 않는다. */
    static PrXaiEvaluationResponseDto forNonRequester(
            PrXaiEvaluationResponseDto response, Collection<Long> sensitiveAmounts) {
        List<PrXaiTopFactorDto> factors =
                orEmpty(response.topFactors()).stream()
                        .map(factor -> publicFactor(factor, sensitiveAmounts))
                        .toList();
        List<PrXaiEvidenceDto> evidence =
                orEmpty(response.supportingEvidence()).stream()
                        .filter(item -> item.field() != null && PRICE_EVIDENCE_FIELDS.contains(item.field()))
                        .filter(item -> !leaks("evidence." + item.field(), item.value(), sensitiveAmounts))
                        // snapshotId 는 작성자의 재무 점수로 만든 해시다. 투표하는 사람에게는 쓸모가 없으니 뺀다.
                        .map(
                                item ->
                                        new PrXaiEvidenceDto(
                                                item.field(),
                                                item.value(),
                                                item.source(),
                                                null,
                                                item.isDefault(),
                                                item.isEstimated(),
                                                item.estimationMethod()))
                        .toList();
        List<String> warnings =
                orEmpty(response.warnings()).stream()
                        .filter(warning -> warning != null && PUBLIC_WARNINGS.contains(warning))
                        .toList();
        String financialStatus =
                response.financialEvaluation() == null || response.financialEvaluation().status() == null
                        ? "unknown"
                        : response.financialEvaluation().status();

        return new PrXaiEvaluationResponseDto(
                response.requestId(),
                response.purchaseRequestId(),
                response.decision(),
                publicSummary(response.decision(), factors),
                new PrXaiSectionDto(financialStatus, List.of()),
                response.priceEvaluation(),
                factors,
                evidence,
                List.of(), // 반사실은 작성자에게 하는 제안이고 금액이 들어 있다
                warnings,
                response.confidence(),
                response.runtimeEngines(),
                response.generatedAt(),
                response.schemaVersion(),
                response.modelVersion(),
                response.ruleVersion(),
                true);
    }

    private static PrXaiTopFactorDto publicFactor(PrXaiTopFactorDto factor, Collection<Long> amounts) {
        String label = leaks("factor." + factor.code(), factor.label(), amounts) ? HIDDEN_TEXT : factor.label();
        boolean priceFactor = factor.code() != null && PRICE_FACTOR_CODES.contains(factor.code());
        // 재무 요인의 영향도는 뺀다: 생활비 구역 요인의 영향도는 사용률(→ 소득)에서 바로 계산된다.
        return new PrXaiTopFactorDto(factor.code(), label, factor.direction(), priceFactor ? factor.impact() : null);
    }

    private static String publicSummary(String decision, List<PrXaiTopFactorDto> factors) {
        String lead = decision == null ? DEFAULT_LEAD : LEAD.getOrDefault(decision, DEFAULT_LEAD);
        if (factors.isEmpty()) {
            return lead;
        }
        String reason = factors.get(0).label();
        return reason == null || reason.isBlank() ? lead : lead + " " + sentence(reason);
    }

    private static String sentence(String text) {
        String trimmed = text.strip();
        char last = trimmed.charAt(trimmed.length() - 1);
        return last == '.' || last == '!' || last == '?' || last == '。' ? trimmed : trimmed + ".";
    }

    /** 작성자의 실제 금액이 숫자로(쉼표 유무 모두) 들어 있으면 true. 값은 로그에 남기지 않는다. */
    private static boolean leaks(String where, String text, Collection<Long> amounts) {
        if (text == null || text.isBlank() || amounts == null || amounts.isEmpty()) {
            return false;
        }
        for (long amount : amounts) {
            if (containsNumber(text, Long.toString(amount))
                    || containsNumber(text, String.format(Locale.US, "%,d", amount))) {
                log.warn("PR XAI 공개 응답에 작성자의 금액이 남아 있어 가렸어요. where={}", where);
                return true;
            }
        }
        return false;
    }

    /** 더 긴 숫자의 일부(예: 1,250,000 안의 250,000)는 같은 수로 치지 않는다. 소수 표기(1250000.0)는 같은 금액이다. */
    private static boolean containsNumber(String text, String number) {
        return Pattern.compile("(?<![0-9,.])" + Pattern.quote(number) + "(?![0-9]|,[0-9])")
                .matcher(text)
                .find();
    }

    private static <T> List<T> orEmpty(List<T> list) {
        return list == null ? List.of() : list;
    }
}
