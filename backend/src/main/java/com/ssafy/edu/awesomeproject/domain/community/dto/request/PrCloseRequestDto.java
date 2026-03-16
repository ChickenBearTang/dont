package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import com.ssafy.edu.awesomeproject.domain.community.entity.PrCloseTargetStatus;
import jakarta.validation.constraints.NotNull;

public record PrCloseRequestDto(@NotNull PrCloseTargetStatus resultStatus) {}
