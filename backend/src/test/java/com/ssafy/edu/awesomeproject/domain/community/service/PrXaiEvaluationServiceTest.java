package com.ssafy.edu.awesomeproject.domain.community.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiEvaluationRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiFinanceProfileDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiProvenanceValueDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiPurchaseContextDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiConfidenceDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiRuntimeEnginesDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiSectionDto;
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
    @Mock private AiClient aiClient;

    private PrXaiEvaluationService prXaiEvaluationService;

    @BeforeEach
    void setUp() {
        prXaiEvaluationService = new PrXaiEvaluationService(prXaiContextService, aiClient);
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
                        "rule-v1");
        when(prXaiContextService.buildContext(67L, 10L)).thenReturn(request);
        when(aiClient.evaluatePrXai("req-123", request)).thenReturn(expected);

        PrXaiEvaluationResponseDto result = prXaiEvaluationService.evaluate(67L, 10L);

        assertThat(result).isSameAs(expected);
    }

    @Test
    void evaluateMapsResourceAccessToGatewayTimeout() {
        PrXaiEvaluationRequestDto request = buildRequest();
        when(prXaiContextService.buildContext(67L, 10L)).thenReturn(request);
        when(aiClient.evaluatePrXai("req-123", request))
                .thenThrow(new ResourceAccessException("timeout"));

        assertThatThrownBy(() -> prXaiEvaluationService.evaluate(67L, 10L))
                .isInstanceOf(CommunityException.class)
                .hasMessageContaining("XAI 평가 응답 시간이 초과되었습니다");
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
                        new PrXaiProvenanceValueDto(250000.0, "spring.finance_profile", "fin-10", false, false, null),
                        new PrXaiProvenanceValueDto(12, "spring.finance_profile", "fin-10", false, false, null)),
                List.of());
    }
}
