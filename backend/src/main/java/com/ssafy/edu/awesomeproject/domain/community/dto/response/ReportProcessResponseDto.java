package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record ReportProcessResponseDto(
        Long reportId,
        String reportStatus,
        Long processedByUserId,
        String processNote,
        LocalDateTime processedAt) {}
