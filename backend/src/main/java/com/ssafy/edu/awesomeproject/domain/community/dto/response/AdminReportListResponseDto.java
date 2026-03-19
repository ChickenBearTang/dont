package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record AdminReportListResponseDto(
        List<ReportSummaryDto> content,
        int page,
        int size,
        long totalElements,
        int totalPages,
        boolean hasNext) {
    public record ReportSummaryDto(
            Long reportId,
            Long reporterUserId,
            String targetType,
            Long targetId,
            String reasonCode,
            String reportStatus,
            LocalDateTime createdAt,
            LocalDateTime processedAt) {}
}
