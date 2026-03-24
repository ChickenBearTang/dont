package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiJustificationResponse(
        @JsonProperty("is_valid") boolean valid, String response) {}
