package com.ssafy.edu.awesomeproject.common.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record ApiResponse<T>(
        @Schema(description = "요청 처리 성공 여부", example = "true") boolean success,
        @Schema(description = "응답 코드", example = "SUCCESS") String code,
        @Schema(description = "응답 메시지", example = "Request processed successfully.") String message,
        @Schema(description = "응답 데이터") T data,
        @Schema(description = "응답 시각 (UTC)", example = "2026-03-03T01:00:00Z")
                OffsetDateTime timestamp) {
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(
                true,
                "SUCCESS",
                "Request processed successfully.",
                data,
                OffsetDateTime.now(ZoneOffset.UTC));
    }

    public static ApiResponse<Void> fail(ErrorCode errorCode) {
        return new ApiResponse<>(
                false,
                errorCode.code(),
                errorCode.message(),
                null,
                OffsetDateTime.now(ZoneOffset.UTC));
    }

    public static <T> ApiResponse<T> fail(ErrorCode errorCode, T data) {
        return new ApiResponse<>(
                false,
                errorCode.code(),
                errorCode.message(),
                data,
                OffsetDateTime.now(ZoneOffset.UTC));
    }
}
