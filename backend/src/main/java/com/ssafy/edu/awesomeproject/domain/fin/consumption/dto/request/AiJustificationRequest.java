package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiJustificationRequest(
        @JsonProperty("user_id") Long userId,
        @JsonProperty("target_month") String targetMonth,
        String message) {}
