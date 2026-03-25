package com.ssafy.edu.awesomeproject.domain.community.dto.response;

public record PrXaiCounterfactualDto(
        String label,
        String targetDecision,
        boolean validated) {}
