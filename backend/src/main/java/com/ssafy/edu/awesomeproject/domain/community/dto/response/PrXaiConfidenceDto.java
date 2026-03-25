package com.ssafy.edu.awesomeproject.domain.community.dto.response;

public record PrXaiConfidenceDto(
        double decisionConfidence,
        double dataCompleteness,
        double explanationFidelity) {}
