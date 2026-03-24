package com.ssafy.edu.awesomeproject.domain.fin.card.dto.response;

import java.util.List;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class AiAnalysisResponse {
    private Map<String, Object> meta;
    private Map<String, Object> overview;
    private List<Map<String, Object>> monthly;
    private Map<String, Object> categories;
    private Map<String, Object> time_patterns;
    private List<Map<String, Object>> cashflow;
    private List<Map<String, Object>> anomalies;
    private AiAnalysisData ai_analysis;

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AiAnalysisData {
        private List<String> consumption_patterns;
        private List<String> anomaly_explanations;
        private List<String> actionable_solutions;
        private String llm_advice;
    }
}
