package com.ssafy.edu.awesomeproject.domain.community.dto.response;

public record PrXaiEvidenceDto(
        String field,
        String value,
        String source,
        String snapshotId,
        boolean isDefault,
        boolean isEstimated,
        String estimationMethod) {}
