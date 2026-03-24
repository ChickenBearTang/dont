package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public record AiMonthlyReportAnalysisResponse(
        @JsonProperty("analysis_payload") Map<String, Object> analysisPayload,
        @JsonProperty("llm_status") String llmStatus,
        @JsonProperty("report_context") Map<String, Object> reportContext) {}
