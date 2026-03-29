package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request;

import jakarta.validation.constraints.NotBlank;

public record GenerateMonthlyReportRequest(@NotBlank String reportMonth) {}
