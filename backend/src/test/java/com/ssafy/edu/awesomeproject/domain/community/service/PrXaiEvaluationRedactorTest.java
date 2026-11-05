package com.ssafy.edu.awesomeproject.domain.community.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiFinanceProfileDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiProvenanceValueDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiConfidenceDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiCounterfactualDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvidenceDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiMetricDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiRuntimeEnginesDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiSectionDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiTopFactorDto;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;

/**
 * 구매 PR 작성자가 아닌 사용자에게는 작성자의 재무 금액이 한 글자도 나가면 안 된다.
 *
 * <p>AI 응답에는 작성자의 금액이 여러 곳에 흩어져 있다 (재무 지표 값, 근거 값, 반사실 문구, 요약 문장의 제안).
 * 게다가 생활비 구역 사용률(예: 84% → 103%)은 금액이 아니어도 공개된 상품 가격과 함께 보면 한도와 소득을 거꾸로 계산할
 * 수 있다 (가격 ÷ 사용률 증가분 = 한도, 한도 × 2 = 소득). 그래서 "금액만 지우기"가 아니라 가격 쪽 항목만 남기는
 * 허용 목록 방식으로 거르고, 응답 전체를 JSON 으로 만들어 작성자의 숫자가 없는지 확인한다.
 */
class PrXaiEvaluationRedactorTest {

    // 작성자의 실제 재무 값 (요청으로 AI 에 보낸 값)
    private static final long CURRENT_BALANCE = 3_000_000L;
    private static final long EMERGENCY_FUND = 800_000L;
    private static final long SAVEBOX = 1_250_000L;
    private static final long CARD_PAYMENT = 410_000L;
    private static final long INCOME = 3_800_000L;
    private static final long FIXED_EXPENSE = 700_000L;
    private static final long SPENDING_30D = 900_000L;
    // 공개된 상품 정보
    private static final long PRICE = 350_000L;
    private static final long AVG_PRICE = 389_000L;

    private static final ObjectMapper JSON = new ObjectMapper().registerModule(new JavaTimeModule());

    private static PrXaiProvenanceValueDto value(Object v) {
        return new PrXaiProvenanceValueDto(v, "spring.test", "snap", false, false, null);
    }

    private static PrXaiFinanceProfileDto authorsFinance() {
        return new PrXaiFinanceProfileDto(
                value((double) CURRENT_BALANCE),
                value((double) EMERGENCY_FUND),
                value((double) SAVEBOX),
                value((double) CARD_PAYMENT),
                value(12),
                value(INCOME),
                value(FIXED_EXPENSE),
                value(SPENDING_30D));
    }

    /** AI 서버가 실제로 만드는 모양의 응답: 작성자의 금액이 곳곳에 들어 있다. */
    private static PrXaiEvaluationResponseDto aiResponse() {
        return new PrXaiEvaluationResponseDto(
                "req-1",
                67L,
                "NOT_RECOMMENDED",
                "지금은 구매를 권하지 않습니다. 이번 구매로 생활비 구역(소득의 50%)을 넘게 됩니다. "
                        + "세이브박스에 100,000원을 더 모으면 구매를 검토할 수 있어요.",
                new PrXaiSectionDto(
                        "caution",
                        List.of(
                                new PrXaiMetricDto("savebox_balance", "세이브박스 잔액", "1,250,000원"),
                                new PrXaiMetricDto("available_fixed_expense", "이번 달 고정지출", "700,000원"),
                                new PrXaiMetricDto("available_fixed_income", "이번 달 고정 수입", "3,800,000원"),
                                new PrXaiMetricDto("budget_zone_limit", "생활비 구역 한도(소득의 50%)", "1,900,000원"),
                                new PrXaiMetricDto("budget_zone_used_before", "구매 전 사용", "1,600,000원 (84%)"),
                                new PrXaiMetricDto("budget_zone_used_after", "구매 후 사용", "1,950,000원 (103%)"),
                                new PrXaiMetricDto("expected_card_payment_amount", "이번 달 카드지출 합계", "410,000원"),
                                new PrXaiMetricDto("days_until_card_due", "카드 결제일까지", "12일"))),
                new PrXaiSectionDto(
                        "favorable",
                        List.of(
                                new PrXaiMetricDto("current_effective_price", "현재 판단 가격", "350,000원"),
                                new PrXaiMetricDto("avg_price_30d", "30일 평균가", "389,000원"))),
                List.of(
                        new PrXaiTopFactorDto(
                                "BUDGET_ZONE_USAGE",
                                "이번 구매로 생활비 구역(소득의 50%)을 넘게 됩니다.",
                                "negative",
                                0.31),
                        new PrXaiTopFactorDto(
                                "BALANCE_AFTER_PURCHASE_TOO_LOW",
                                "구매 후 예상 잔액이 낮아질 가능성이 큽니다.",
                                "negative",
                                0.22),
                        new PrXaiTopFactorDto(
                                "PRICE_RELATIVE_TO_30D_AVG",
                                "현재 가격이 최근 30일 평균가보다 낮아 유리합니다.",
                                "positive",
                                0.18)),
                List.of(
                        evidence("budget_zone_usage", "1.0263", "fastapi.xai"),
                        evidence("projected_balance_after_purchase", "900000", "fastapi.xai"),
                        evidence("emergency_fund_balance", "800000", "fastapi.xai"),
                        evidence("current_price", "350000", "spring.pr_post"),
                        evidence("avg_price_30d", "389000", "fastapi.xai"),
                        evidence("monthly_spending_30d", "900000", "fastapi.input_contract")),
                List.of(
                        new PrXaiCounterfactualDto(
                                "세이브박스를 100,000원 더 모으면 구매를 검토할 수 있어요.", "REVIEW", true)),
                List.of(
                        "NO_PRICE_HISTORY",
                        "FINANCE_FIELD_ESTIMATED:available_fixed_income",
                        "BUDGET_RULE_UNAVAILABLE:spending_unknown",
                        "EMERGENCY_COVER_LOW",
                        "CRAWLED_PRICE_DIVERGES_FROM_REQUEST"),
                new PrXaiConfidenceDto(0.81, 0.92, 0.88),
                new PrXaiRuntimeEnginesDto("rule_engine_v1", "rule_trace", "enabled", "enabled"),
                OffsetDateTime.of(2026, 3, 24, 18, 0, 0, 0, ZoneOffset.UTC),
                "v1",
                null,
                "rule-v1",
                false);
    }

    private static PrXaiEvidenceDto evidence(String field, String value, String source) {
        return new PrXaiEvidenceDto(field, value, source, "snap", false, false, null);
    }

    private static PrXaiEvaluationResponseDto redacted() {
        return PrXaiEvaluationRedactor.forNonRequester(
                aiResponse(), PrXaiEvaluationRedactor.sensitiveAmounts(authorsFinance()));
    }

    @Test
    void noneOfTheAuthorsNumbersAppearAnywhereInThePublicResponse() throws Exception {
        String json = JSON.writeValueAsString(redacted());

        // 작성자의 값과, 거기서 파생된 값(한도, 구매 전후 사용액, 제안 금액, 구매 후 잔액)을 쉼표 유무 모두 찾는다.
        for (long secret :
                new long[] {
                    CURRENT_BALANCE, EMERGENCY_FUND, SAVEBOX, CARD_PAYMENT, INCOME, FIXED_EXPENSE, SPENDING_30D,
                    1_900_000L, 1_600_000L, 1_950_000L, 100_000L
                }) {
            assertThat(json).as("plain %d", secret).doesNotContain(Long.toString(secret));
            assertThat(json).as("grouped %d", secret).doesNotContain(String.format("%,d", secret));
        }
        // 사용률(84% → 103%)과 사용률 원값(1.0263)도 가격과 함께 소득을 드러내므로 나가면 안 된다.
        assertThat(json).doesNotContain("84%").doesNotContain("103%").doesNotContain("1.0263");
        // 공개된 상품 가격은 그대로다.
        assertThat(json).contains("350,000원").contains("389,000원");
    }

    @Test
    void thePublicViewKeepsWhatVotersNeedAndDropsTheRest() {
        PrXaiEvaluationResponseDto source = aiResponse();
        PrXaiEvaluationResponseDto view = redacted();

        assertThat(view.financialDetailsHidden()).isTrue();
        assertThat(view.decision()).isEqualTo("NOT_RECOMMENDED");
        assertThat(view.requestId()).isEqualTo("req-1");
        assertThat(view.confidence()).isEqualTo(source.confidence());
        assertThat(view.runtimeEngines()).isEqualTo(source.runtimeEngines());

        // 재무 지표 전부와 반사실(작성자에게 하는 제안)은 없다. 상태(caution 등)만 남는다.
        assertThat(view.financialEvaluation().status()).isEqualTo("caution");
        assertThat(view.financialEvaluation().keyMetrics()).isEmpty();
        assertThat(view.counterfactuals()).isEmpty();

        // 가격 평가는 공개된 상품 정보라서 그대로다.
        assertThat(view.priceEvaluation()).isEqualTo(source.priceEvaluation());

        // 근거는 가격 쪽만.
        assertThat(view.supportingEvidence())
                .extracting(PrXaiEvidenceDto::field)
                .containsExactly("current_price", "avg_price_30d");
        // 스냅샷 ID 는 작성자의 재무 점수로 만든 해시라서 내려 주지 않는다.
        assertThat(view.supportingEvidence()).extracting(PrXaiEvidenceDto::snapshotId).containsOnlyNulls();

        // 경고는 가격·수집 관련만. 재무 입력 경고(추정, 예산 불가, 비상금)는 작성자의 사정을 말해 주므로 뺀다.
        assertThat(view.warnings()).containsExactly("NO_PRICE_HISTORY", "CRAWLED_PRICE_DIVERGES_FROM_REQUEST");
    }

    @Test
    void financeFactorsKeepTheirReasonButNotTheirInfluence() {
        PrXaiEvaluationResponseDto view = redacted();

        // 이유 문장(숫자 없는 고정 문구)은 투표하는 사람에게 필요해서 남긴다.
        assertThat(view.topFactors()).extracting(PrXaiTopFactorDto::code).containsExactly(
                "BUDGET_ZONE_USAGE", "BALANCE_AFTER_PURCHASE_TOO_LOW", "PRICE_RELATIVE_TO_30D_AVG");
        assertThat(view.topFactors().get(0).label()).isEqualTo("이번 구매로 생활비 구역(소득의 50%)을 넘게 됩니다.");
        // 하지만 생활비 구역 요인의 영향도는 사용률에서 바로 계산되므로(사용률 ↔ 영향도) 재무 요인의 영향도는 뺀다.
        assertThat(view.topFactors().get(0).impact()).isNull();
        assertThat(view.topFactors().get(1).impact()).isNull();
        // 가격 요인의 영향도는 상품 정보라서 그대로다.
        assertThat(view.topFactors().get(2).impact()).isEqualTo(0.18);
    }

    @Test
    void summaryIsRebuiltFromTheVerdictAndTheFirstReasonNotFromAiText() {
        // AI 요약에는 반사실 제안("100,000원을 더 모으면")이 이어 붙는다. 공개 요약은 판정 문장과 첫 이유만이다.
        assertThat(redacted().summary())
                .isEqualTo("지금은 구매를 권하지 않습니다. 이번 구매로 생활비 구역(소득의 50%)을 넘게 됩니다.");
    }

    @Test
    void anAuthorNumberThatSlipsIntoAKeptTextIsStillCaught() throws Exception {
        // 앞으로 AI 가 요인 문구나 근거 값에 작성자의 금액을 넣게 바뀌어도 그대로 나가지 않는다 (마지막 방어선).
        PrXaiEvaluationResponseDto source = aiResponse();
        PrXaiEvaluationResponseDto drifted =
                new PrXaiEvaluationResponseDto(
                        source.requestId(),
                        source.purchaseRequestId(),
                        source.decision(),
                        source.summary(),
                        source.financialEvaluation(),
                        source.priceEvaluation(),
                        List.of(
                                new PrXaiTopFactorDto(
                                        "PRICE_RELATIVE_TO_30D_AVG",
                                        "세이브박스 1,250,000원으로는 부족해요.",
                                        "negative",
                                        0.2)),
                        List.of(evidence("current_price", "1250000", "spring.pr_post")),
                        source.counterfactuals(),
                        source.warnings(),
                        source.confidence(),
                        source.runtimeEngines(),
                        source.generatedAt(),
                        source.schemaVersion(),
                        source.modelVersion(),
                        source.ruleVersion(),
                        false);

        PrXaiEvaluationResponseDto view =
                PrXaiEvaluationRedactor.forNonRequester(
                        drifted, PrXaiEvaluationRedactor.sensitiveAmounts(authorsFinance()));
        String json = JSON.writeValueAsString(view);

        assertThat(json).doesNotContain("1,250,000").doesNotContain("1250000");
        assertThat(view.supportingEvidence()).isEmpty();
        assertThat(view.topFactors()).hasSize(1);
        assertThat(view.summary()).doesNotContain("1,250,000");
    }

    @Test
    void smallNumbersAreNotMistakenForSecretsAndNullPartsDoNotBreakIt() {
        // 12일, 30일 같은 작은 수는 금액이 아니다 (1000 미만은 대조하지 않는다).
        assertThat(PrXaiEvaluationRedactor.sensitiveAmounts(authorsFinance()))
                .containsExactlyInAnyOrder(
                        CURRENT_BALANCE, EMERGENCY_FUND, SAVEBOX, CARD_PAYMENT, INCOME, FIXED_EXPENSE, SPENDING_30D);

        PrXaiEvaluationResponseDto sparse =
                new PrXaiEvaluationResponseDto(
                        "req-2", 1L, "REVIEW", null, null, null, null, null, null, null, null, null, null, null,
                        null, null, false);
        PrXaiEvaluationResponseDto view =
                PrXaiEvaluationRedactor.forNonRequester(sparse, List.of());

        assertThat(view.financialDetailsHidden()).isTrue();
        assertThat(view.topFactors()).isEmpty();
        assertThat(view.supportingEvidence()).isEmpty();
        assertThat(view.counterfactuals()).isEmpty();
        assertThat(view.warnings()).isEmpty();
        assertThat(view.summary()).isEqualTo("구매 전에 한 번 더 검토해 보세요.");
    }

    @Test
    void responseFromTheAiServerWithoutTheFlagDeserializesAsNotHidden() throws Exception {
        // AI 서버는 financialDetailsHidden 을 보내지 않는다. 없으면 false 여야 작성자 응답이 그대로 나간다.
        String fromAi =
                "{\"requestId\":\"r\",\"purchaseRequestId\":1,\"decision\":\"BUY_NOW\",\"summary\":\"s\","
                        + "\"financialEvaluation\":{\"status\":\"healthy\",\"keyMetrics\":[]},"
                        + "\"topFactors\":[{\"code\":\"X\",\"label\":\"l\",\"direction\":\"positive\",\"impact\":0.4}],"
                        + "\"warnings\":[]}";

        PrXaiEvaluationResponseDto parsed = JSON.readValue(fromAi, PrXaiEvaluationResponseDto.class);

        assertThat(parsed.financialDetailsHidden()).isFalse();
        assertThat(parsed.topFactors().get(0).impact()).isEqualTo(0.4);
    }
}
