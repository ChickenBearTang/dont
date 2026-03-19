package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import com.ssafy.edu.awesomeproject.domain.community.entity.ReportReasonCode;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReportTargetType;
import jakarta.validation.constraints.NotNull;

public record ReportCreateRequestDto(
        @NotNull ReportTargetType targetType,
        @NotNull Long targetId,
        @NotNull ReportReasonCode reasonCode,
        String detailText) {}
