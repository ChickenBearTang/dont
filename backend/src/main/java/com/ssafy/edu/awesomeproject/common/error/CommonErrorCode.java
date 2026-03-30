package com.ssafy.edu.awesomeproject.common.error;

import org.springframework.http.HttpStatus;

public enum CommonErrorCode implements ErrorCode {
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "COMMON_400_1", "잘못된 입력입니다."),
    VALIDATION_FAILED(HttpStatus.BAD_REQUEST, "COMMON_400_2", "유효성 검증에 실패했습니다."),
    PAYLOAD_TOO_LARGE(HttpStatus.PAYLOAD_TOO_LARGE, "COMMON_413_1", "요청 본문이 너무 큽니다."),
    RESOURCE_NOT_FOUND(HttpStatus.NOT_FOUND, "COMMON_404_1", "리소스를 찾을 수 없습니다."),
    BUSINESS_RULE_VIOLATION(HttpStatus.CONFLICT, "COMMON_409_1", "비즈니스 규칙 위반입니다."),
    INTERNAL_SERVER_ERROR(
            HttpStatus.INTERNAL_SERVER_ERROR, "COMMON_500_1", "예기치 않은 서버 오류가 발생했습니다.");

    private final HttpStatus status;
    private final String code;
    private final String message;

    CommonErrorCode(HttpStatus status, String code, String message) {
        this.status = status;
        this.code = code;
        this.message = message;
    }

    @Override
    public HttpStatus status() {
        return status;
    }

    @Override
    public String code() {
        return code;
    }

    @Override
    public String message() {
        return message;
    }
}
