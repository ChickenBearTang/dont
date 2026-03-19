package com.ssafy.edu.awesomeproject.common.error;

import io.swagger.v3.oas.annotations.media.Schema;

public record ValidationError(
        @Schema(description = "유효성 검증 실패 필드명", example = "message") String field,
        @Schema(description = "유효성 검증 실패 사유", example = "message must not be blank.")
                String reason) {}
