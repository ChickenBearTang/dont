package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record PrXaiProvenanceValueDto(
        Object value,
        String source,
        String snapshotId,
        boolean isDefault,
        boolean isEstimated,
        String estimationMethod) {}
