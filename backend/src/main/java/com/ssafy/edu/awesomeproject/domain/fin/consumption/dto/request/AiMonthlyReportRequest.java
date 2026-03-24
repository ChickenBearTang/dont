package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiMonthlyReportRequest(
        @JsonProperty("user_id") Long userId, @JsonProperty("report_month") String reportMonth) {}
