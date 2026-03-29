package com.ssafy.edu.awesomeproject.domain.fin.consumption.client;

import java.util.Map;

public interface ConsumptionAiClient {
    AiReportAnalysis analyzeMonthlyReport(Long userId, String reportMonth);

    JustificationEvaluation evaluateJustification(Long userId, String targetMonth, String message);

    record AiReportAnalysis(Map<String, Object> analysisPayload, String llmStatus) {}

    record JustificationEvaluation(boolean valid, String response) {}
}
