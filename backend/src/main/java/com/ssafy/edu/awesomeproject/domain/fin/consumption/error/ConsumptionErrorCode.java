package com.ssafy.edu.awesomeproject.domain.fin.consumption.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum ConsumptionErrorCode implements ErrorCode {
    INVALID_REPORT_MONTH(
            HttpStatus.BAD_REQUEST, "CONS_400_1", "reportMonth must be yyyy-MM format."),
    REPORT_NOT_FOUND(HttpStatus.NOT_FOUND, "CONS_404_1", "Monthly consumption report not found."),
    INVALID_PAYLOAD(HttpStatus.BAD_REQUEST, "CONS_400_2", "Invalid consumption request payload.");

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
