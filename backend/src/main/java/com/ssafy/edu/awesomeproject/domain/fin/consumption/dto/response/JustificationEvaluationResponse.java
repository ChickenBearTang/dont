package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response;

import java.time.LocalDateTime;

public record JustificationEvaluationResponse(
        Long id,
        String targetMonth,
        boolean valid,
        String userMessage,
        String aiResponse,
        LocalDateTime createdAt,
        boolean reportRegenerated,
        MonthlyReportResponse regeneratedReport) {}
