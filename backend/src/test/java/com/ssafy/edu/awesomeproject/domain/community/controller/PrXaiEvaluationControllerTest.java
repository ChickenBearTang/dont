package com.ssafy.edu.awesomeproject.domain.community.controller;

import static org.hamcrest.Matchers.hasSize;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ssafy.edu.awesomeproject.common.error.GlobalExceptionHandler;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserIdArgumentResolver;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserInterceptor;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiConfidenceDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiCounterfactualDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvidenceDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiMetricDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiRuntimeEnginesDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiSectionDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiTopFactorDto;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.service.PrXaiEvaluationService;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@ExtendWith(MockitoExtension.class)
class PrXaiEvaluationControllerTest {

    @Mock private PrXaiEvaluationService prXaiEvaluationService;

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        PrXaiEvaluationController controller = new PrXaiEvaluationController(prXaiEvaluationService);
        mockMvc =
                MockMvcBuilders.standaloneSetup(controller)
                        .setControllerAdvice(new GlobalExceptionHandler())
                        .setCustomArgumentResolvers(new CurrentUserIdArgumentResolver())
                        .build();
    }

    @Test
    void getXaiEvaluationReturnsWrappedSuccessPayload() throws Exception {
        PrXaiEvaluationResponseDto responseDto =
                new PrXaiEvaluationResponseDto(
                        "req-123",
                        67L,
                        "BUY_NOW",
                        "지금 구매해도 무리가 적습니다.",
                        new PrXaiSectionDto(
                                "healthy",
                                List.of(new PrXaiMetricDto("balance", "현재 잔액", "1,500,000원"))),
                        new PrXaiSectionDto(
                                "favorable",
                                List.of(new PrXaiMetricDto("price_gap", "최근 시세 대비", "-8%"))),
                        List.of(new PrXaiTopFactorDto("price_gap", "가격 메리트", "positive", 0.42)),
                        List.of(
                                new PrXaiEvidenceDto(
                                        "days_until_card_due",
                                        "14",
                                        "spring.finance_profile",
                                        "snapshot-1",
                                        false,
                                        false,
                                        null)),
                        List.of(new PrXaiCounterfactualDto("가격이 5% 상승하면 WAIT로 바뀔 수 있습니다.", "WAIT", true)),
                        List.of("PRICE_HISTORY_SHORT_WINDOW"),
                        new PrXaiConfidenceDto(0.81, 0.92, 0.88),
                        new PrXaiRuntimeEnginesDto("rule_engine_v1", "rule_trace", "enabled", "enabled"),
                        OffsetDateTime.of(2026, 3, 24, 18, 0, 0, 0, ZoneOffset.UTC),
                        "v1",
                        null,
                        "rule-v1");
        when(prXaiEvaluationService.evaluate(67L, 10L)).thenReturn(responseDto);

        mockMvc.perform(
                        get("/community/purchase-requests/{postId}/xai-evaluation", 67L)
                                .requestAttr(CurrentUserInterceptor.CURRENT_USER_ID_ATTR, 10L))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.data.requestId").value("req-123"))
                .andExpect(jsonPath("$.data.purchaseRequestId").value(67))
                .andExpect(jsonPath("$.data.decision").value("BUY_NOW"))
                .andExpect(jsonPath("$.data.summary").value("지금 구매해도 무리가 적습니다."))
                .andExpect(jsonPath("$.data.topFactors", hasSize(1)))
                .andExpect(jsonPath("$.data.supportingEvidence", hasSize(1)))
                .andExpect(jsonPath("$.data.counterfactuals", hasSize(1)))
                .andExpect(jsonPath("$.data.warnings", hasSize(1)))
                .andExpect(jsonPath("$.data.confidence.decisionConfidence").value(0.81))
                .andExpect(jsonPath("$.data.runtimeEngines.decision").value("rule_engine_v1"));
    }

    @Test
    void getXaiEvaluationReturnsUnauthorizedWhenCurrentUserMissing() throws Exception {
        mockMvc.perform(get("/community/purchase-requests/{postId}/xai-evaluation", 67L))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("TOKEN_401_1"));
    }

    @Test
    void getXaiEvaluationReturnsNotFoundWhenServiceThrows() throws Exception {
        when(prXaiEvaluationService.evaluate(67L, 10L))
                .thenThrow(new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_NOT_FOUND));

        mockMvc.perform(
                        get("/community/purchase-requests/{postId}/xai-evaluation", 67L)
                                .requestAttr(CurrentUserInterceptor.CURRENT_USER_ID_ATTR, 10L))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("PR_404_1"));
    }
}
