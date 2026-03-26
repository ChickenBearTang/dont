package com.ssafy.edu.awesomeproject.domain.community.dto.response;

public record PrXaiAvailabilityResponseDto(
        boolean enabled,
        String reason,
        String matchType,
        String matchedItemTitle,
        String matchedItemUrl) {}
