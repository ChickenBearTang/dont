package com.ssafy.edu.awesomeproject.domain.fin.consumption.client;

import java.util.List;
import java.util.Map;

public interface ConsumptionAiClient {
    AiReportAnalysis analyzeMonthlyReport(Map<String, Object> reportPayload);

    JustificationEvaluation evaluateJustification(
            String message, Map<String, Object> context, List<Map<String, String>> history);

    record AiReportAnalysis(
            Map<String, Object> analysisPayload,
            String llmStatus) {}

    record JustificationEvaluation(
            boolean valid,
            String response) {}
}
