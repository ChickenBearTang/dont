package com.ssafy.edu.awesomeproject.domain.community.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiEvaluationRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiFinanceProfileDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiProvenanceValueDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiPurchaseContextDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiAvailabilityResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiConfidenceDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiCounterfactualDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiMetricDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiRuntimeEnginesDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiSectionDto;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.client.ResourceAccessException;

@ExtendWith(MockitoExtension.class)
class PrXaiEvaluationServiceTest {

    @Mock private PrXaiContextService prXaiContextService;
    @Mock private PrXaiAvailabilityService prXaiAvailabilityService;
    @Mock private AiClient aiClient;

    private PrXaiEvaluationService prXaiEvaluationService;

    @BeforeEach
    void setUp() {
        prXaiEvaluationService =
                new PrXaiEvaluationService(prXaiContextService, prXaiAvailabilityService, aiClient);
    }

    private static PrXaiAvailabilityResponseDto available() {
        return new PrXaiAvailabilityResponseDto(true, "ok", "URL_EXACT", "title", "https://example.com");
    }

    @Test
    void evaluateDelegatesToAiClientWithRequestId() {
        PrXaiEvaluationRequestDto request = buildRequest();
        PrXaiEvaluationResponseDto expected =
                new PrXaiEvaluationResponseDto(
                        "req-123",
                        67L,
                        "REVIEW",
                        "요약",
                        new PrXaiSectionDto("ok", List.of()),
                        new PrXaiSectionDto("ok", List.of()),
                        List.of(),
                        List.of(),
                        List.of(),
                        List.of(),
                        new PrXaiConfidenceDto(0.7, 0.8, 0.9),
                        new PrXaiRuntimeEnginesDto("rule_engine_v1", "rule_trace", "disabled", "disabled"),
                        OffsetDateTime.of(2026, 3, 25, 0, 0, 0, 0, ZoneOffset.UTC),
                        "v1",
                        null,
                        "rule-v1",
                        false);
        when(prXaiAvailabilityService.checkAvailability(67L, 10L)).thenReturn(available());
        when(prXaiContextService.buildContext(67L, 10L)).thenReturn(request);
        when(prXaiContextService.isPurchaseRequester(67L, 10L)).thenReturn(true);
        when(aiClient.evaluatePrXai("req-123", request)).thenReturn(expected);

        PrXaiEvaluationResponseDto result = prXaiEvaluationService.evaluate(67L, 10L);

        assertThat(result).isSameAs(expected);
    }

    @Test
    void someoneWhoIsNotThePostAuthorNeverReceivesTheAuthorsAmounts() throws Exception {
        // buildRequest() 의 작성자 값: 잔액 3,000,000 / 비상금 800,000 / 세이브박스 800,000 / 카드 250,000
        PrXaiEvaluationRequestDto request = buildRequest();
        PrXaiEvaluationResponseDto fromAi =
                new PrXaiEvaluationResponseDto(
                        "req-123",
                        67L,
                        "WAIT",
                        "조금 더 지켜보는 것을 권합니다. 구매 후 예상 잔액이 낮아질 가능성이 큽니다. "
                                + "세이브박스 800,000원에 200,000원을 더 모으면 구매를 검토할 수 있어요.",
                        new PrXaiSectionDto(
                                "caution",
                                List.of(new PrXaiMetricDto("savebox_balance", "세이브박스 잔액", "800,000원"))),
                        new PrXaiSectionDto(
                                "favorable",
                                List.of(new PrXaiMetricDto("current_effective_price", "현재 판단 가격", "2,500,000원"))),
                        List.of(),
                        List.of(),
                        List.of(new PrXaiCounterfactualDto("세이브박스를 200,000원 더 모으면 구매를 검토할 수 있어요.", "REVIEW", true)),
                        List.of("FINANCE_FIELD_ESTIMATED:available_fixed_income", "NO_PRICE_HISTORY"),
                        new PrXaiConfidenceDto(0.7, 0.8, 0.9),
                        new PrXaiRuntimeEnginesDto("rule_engine_v1", "rule_trace", "disabled", "disabled"),
                        OffsetDateTime.of(2026, 3, 25, 0, 0, 0, 0, ZoneOffset.UTC),
                        "v1",
                        null,
                        "rule-v1",
                        false);
        // 다른 사용자(11)가 조회한다. isPurchaseRequester 는 stub 하지 않아 false (= 확인이 안 되면 가린다).
        when(prXaiAvailabilityService.checkAvailability(67L, 11L)).thenReturn(available());
        when(prXaiContextService.buildContext(67L, 11L)).thenReturn(request);
        when(aiClient.evaluatePrXai("req-123", request)).thenReturn(fromAi);

        PrXaiEvaluationResponseDto result = prXaiEvaluationService.evaluate(67L, 11L);

        assertThat(result.financialDetailsHidden()).isTrue();
        assertThat(result.financialEvaluation().keyMetrics()).isEmpty();
        assertThat(result.counterfactuals()).isEmpty();
        assertThat(result.warnings()).containsExactly("NO_PRICE_HISTORY");
        // 상품 가격 평가는 공개 정보라서 그대로다.
        assertThat(result.priceEvaluation()).isEqualTo(fromAi.priceEvaluation());
        String json = new ObjectMapper().registerModule(new JavaTimeModule()).writeValueAsString(result);
        assertThat(json)
                .doesNotContain("800,000")
                .doesNotContain("200,000")
                .doesNotContain("3,000,000")
                .doesNotContain("3000000")
                .contains("2,500,000원");
    }

    @Test
    void evaluateMapsResourceAccessToGatewayTimeout() {
        PrXaiEvaluationRequestDto request = buildRequest();
        when(prXaiAvailabilityService.checkAvailability(67L, 10L)).thenReturn(available());
        when(prXaiContextService.buildContext(67L, 10L)).thenReturn(request);
        when(aiClient.evaluatePrXai("req-123", request))
                .thenThrow(new ResourceAccessException("timeout"));

        assertThatThrownBy(() -> prXaiEvaluationService.evaluate(67L, 10L))
                .isInstanceOf(CommunityException.class)
                .hasMessageContaining("XAI 평가 응답 시간이 초과되었습니다");
    }

    @Test
    void evaluateRejectsUnsupportedItemWithItsOwnErrorCodeAndKoreanReason() {
        String reason = "현재 XAI 평가는 F87, VXE R1, MX Master 3S 품목만 지원해요.";
        when(prXaiAvailabilityService.checkAvailability(67L, 10L))
                .thenReturn(new PrXaiAvailabilityResponseDto(false, reason, "ITEM_WHITELIST_ONLY", null, null));

        assertThatThrownBy(() -> prXaiEvaluationService.evaluate(67L, 10L))
                .isInstanceOfSatisfying(
                        CommunityException.class,
                        exception -> {
                            // '열려있는 PR에서만 투표할 수 있습니다'(PR_409_2)로 나가던 오류다.
                            assertThat(exception.getErrorCode())
                                    .isEqualTo(CommunityErrorCode.PURCHASE_REQUEST_XAI_UNSUPPORTED);
                            assertThat(exception.getErrorCode().code()).isEqualTo("PR_422_1");
                            assertThat(exception.getDetails()).isEqualTo(reason);
                        });
        verifyNoInteractions(prXaiContextService, aiClient);
    }

    private PrXaiEvaluationRequestDto buildRequest() {
        return new PrXaiEvaluationRequestDto(
                "req-123",
                "v1",
                "v1",
                new PrXaiPurchaseContextDto(
                        67L,
                        "맥북 구매 요청",
                        "맥북 프로",
                        "개발용",
                        "IT",
                        "https://example.com/macbook",
                        new PrXaiProvenanceValueDto(2500000L, "spring.pr_post", "pr-67", false, false, null)),
                new PrXaiFinanceProfileDto(
                        new PrXaiProvenanceValueDto(3000000.0, "spring.finance_profile", "fin-10", false, false, null),
                        new PrXaiProvenanceValueDto(800000.0, "spring.finance_profile", "fin-10", false, false, null),
                        new PrXaiProvenanceValueDto(800000.0, "spring.savebox", "savebox-10", false, false, null),
                        new PrXaiProvenanceValueDto(250000.0, "spring.finance_profile", "fin-10", false, false, null),
                        new PrXaiProvenanceValueDto(12, "spring.finance_profile", "fin-10", false, false, null),
                        null,
                        null,
                        null),
                List.of());
    }
}
