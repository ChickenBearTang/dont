package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response;

import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.MonthlyReportGenerationSource;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.MonthlyReportLlmStatus;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.MonthlyReportStatus;
import java.time.LocalDateTime;
import java.util.Map;

public record MonthlyReportResponse(
        Long id,
        String reportMonth,
        Integer versionNo,
        boolean latest,
        MonthlyReportLlmStatus llmStatus,
        MonthlyReportStatus reportStatus,
        MonthlyReportGenerationSource generationSource,
        LocalDateTime generatedAt,
        Map<String, Object> reportPayload) {}
