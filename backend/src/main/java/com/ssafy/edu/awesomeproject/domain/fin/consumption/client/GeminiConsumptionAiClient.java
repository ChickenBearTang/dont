package com.ssafy.edu.awesomeproject.domain.fin.consumption.client;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Slf4j
@Component
@RequiredArgsConstructor
public class GeminiConsumptionAiClient implements ConsumptionAiClient {

    private static final String DEFAULT_MODEL = "gemini-2.5-flash";

    private final ObjectMapper objectMapper;

    @Value("${GEMINI_API_KEY:}")
    private String apiKey;

    @Value("${AI_GEMINI_MODEL:" + DEFAULT_MODEL + "}")
    private String model;

    @Value("${AI_GEMINI_BASE_URL:https://generativelanguage.googleapis.com}")
    private String baseUrl;

    @Override
    public AiReportAnalysis analyzeMonthlyReport(Map<String, Object> reportPayload) {
        if (apiKey == null || apiKey.isBlank()) {
            log.warn(
                    "Gemini report analysis skipped: GEMINI_API_KEY is missing. Fallback analysis will be used.");
            return new AiReportAnalysis(defaultReportFeedback(), "degraded");
        }

        String prompt =
                """
                You are a financial analyst.
                Read the monthly card summary JSON and return only strict JSON with:
                - consumption_patterns: string[]
                - anomaly_explanations: string[]
                - actionable_solutions: string[]
                Answer in Korean.

                Data:
                """
                        + toJson(reportPayload);

        try {
            String raw = generateContent(prompt);
            Map<String, Object> parsed = parseJsonObject(raw);

            Map<String, Object> aiPayload =
                    Map.of(
                            "consumption_patterns",
                                    castStringList(parsed.get("consumption_patterns")),
                            "anomaly_explanations",
                                    castStringList(parsed.get("anomaly_explanations")),
                            "actionable_solutions",
                                    castStringList(parsed.get("actionable_solutions")));

            log.info("Gemini report analysis succeeded with model={}", model);
            return new AiReportAnalysis(aiPayload, "ok");
        } catch (Exception exception) {
            log.warn(
                    "Gemini report analysis failed. Fallback analysis will be used. reason={}: {}",
                    exception.getClass().getSimpleName(),
                    exception.getMessage());
            return new AiReportAnalysis(defaultReportFeedback(), "degraded");
        }
    }

    @Override
    public JustificationEvaluation evaluateJustification(
            String message, Map<String, Object> context, List<Map<String, String>> history) {
        if (apiKey == null || apiKey.isBlank()) {
            return new JustificationEvaluation(
                    false, "AI key is missing. 현재는 변명 분석 기능을 사용할 수 없습니다.");
        }

        String prompt =
                """
                You are a financial advisor.
                Evaluate if the user's spending justification is valid.
                Return only strict JSON:
                {
                  "is_valid": true or false,
                  "response": "short Korean feedback"
                }

                Context:
                """
                        + toJson(context)
                        + "\nHistory:\n"
                        + toJson(history)
                        + "\nUser message:\n"
                        + message;

        try {
            String raw = generateContent(prompt);
            Map<String, Object> parsed = parseJsonObject(raw);
            boolean valid = Boolean.TRUE.equals(parsed.get("is_valid"));
            String response =
                    parsed.get("response") == null
                            ? "분석 결과를 생성하지 못했습니다."
                            : String.valueOf(parsed.get("response"));
            return new JustificationEvaluation(valid, response);
        } catch (Exception exception) {
            log.warn("Gemini justification evaluation failed: {}", exception.getMessage());
            return new JustificationEvaluation(false, "변명 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
        }
    }

    private String generateContent(String prompt) {
        RestClient client = RestClient.builder().baseUrl(baseUrl).build();

        Map<String, Object> body =
                Map.of("contents", List.of(Map.of("parts", List.of(Map.of("text", prompt)))));

        JsonNode node =
                client.post()
                        .uri("/v1beta/models/{model}:generateContent?key={key}", model, apiKey)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(body)
                        .retrieve()
                        .body(JsonNode.class);

        if (node == null) {
            throw new IllegalStateException("Gemini response is null");
        }

        JsonNode textNode =
                node.path("candidates").path(0).path("content").path("parts").path(0).path("text");
        String text = textNode.asText("");
        if (text.isBlank()) {
            throw new IllegalStateException("Gemini response text is empty");
        }
        return text;
    }

    private Map<String, Object> parseJsonObject(String rawText) {
        String text = rawText.trim();
        if (text.startsWith("```")) {
            int start = text.indexOf('{');
            int end = text.lastIndexOf('}');
            if (start >= 0 && end > start) {
                text = text.substring(start, end + 1);
            }
        }

        try {
            return objectMapper.readValue(text, new TypeReference<>() {});
        } catch (Exception exception) {
            throw new IllegalArgumentException("Failed to parse AI JSON response", exception);
        }
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception exception) {
            return "{}";
        }
    }

    private List<String> castStringList(Object value) {
        if (!(value instanceof List<?> raw)) {
            return List.of();
        }
        return raw.stream().map(String::valueOf).toList();
    }

    private Map<String, Object> defaultReportFeedback() {
        return Map.of(
                "consumption_patterns", List.of("카드 소비 요약 분석은 가능하지만 AI 상세 해석은 현재 제한됩니다."),
                "anomaly_explanations", List.of(),
                "actionable_solutions", List.of("카테고리 상위 지출부터 우선 절감 목표를 설정해보세요."));
    }
}
