package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record ReportCreateResponseDto(
        Long reportId, String reportStatus, LocalDateTime createdAt) {}
