package com.ssafy.edu.awesomeproject.domain.fin.consumption.client;

import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request.AiMonthlyReportRequest;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.AiMonthlyReportAnalysisResponse;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class PythonConsumptionAiClient implements ConsumptionAiClient {

    private final AiClient aiClient;

    @Override
    public AiReportAnalysis analyzeMonthlyReport(Long userId, String reportMonth) {
        try {
            AiMonthlyReportAnalysisResponse response =
                    aiClient.analyzeMonthlyReport(new AiMonthlyReportRequest(userId, reportMonth));
            if (response == null || response.analysisPayload() == null) {
                throw new IllegalStateException("AI monthly report response is empty");
            }
            return new AiReportAnalysis(response.analysisPayload(), response.llmStatus());
        } catch (Exception exception) {
            log.warn(
                    "Python monthly report analysis failed. Falling back to degraded response. reason={}",
                    exception.getMessage());
            return new AiReportAnalysis(defaultReportFeedback(), "degraded");
        }
    }

    private Map<String, Object> defaultReportFeedback() {
        return Map.of(
                "consumption_patterns", List.of("AI 소비 리포트를 생성하지 못해 기본 분석만 제공하고 있습니다."),
                "anomaly_explanations", List.of(),
                "actionable_solutions", List.of("잠시 후 다시 시도하거나 지출 데이터를 확인해주세요."));
    }
}
