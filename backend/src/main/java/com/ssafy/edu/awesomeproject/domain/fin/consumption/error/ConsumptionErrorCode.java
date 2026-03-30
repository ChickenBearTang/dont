package com.ssafy.edu.awesomeproject.domain.fin.consumption.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum ConsumptionErrorCode implements ErrorCode {
    INVALID_REPORT_MONTH(
            HttpStatus.BAD_REQUEST, "CONS_400_1", "reportMonth must be yyyy-MM format."),
    REPORT_NOT_FOUND(HttpStatus.NOT_FOUND, "CONS_404_1", "월간 소비 리포트를 찾을 수 없습니다."),
    INVALID_PAYLOAD(HttpStatus.BAD_REQUEST, "CONS_400_2", "소비 분석 요청 페이로드가 올바르지 않습니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

    ConsumptionErrorCode(HttpStatus httpStatus, String code, String message) {
        this.httpStatus = httpStatus;
        this.code = code;
        this.message = message;
    }

    @Override
    public HttpStatus status() {
        return httpStatus;
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
