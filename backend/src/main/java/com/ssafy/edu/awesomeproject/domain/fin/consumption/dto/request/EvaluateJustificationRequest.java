package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request;

import jakarta.validation.constraints.NotBlank;

public record EvaluateJustificationRequest(
        @NotBlank String targetMonth, @NotBlank String message) {}
