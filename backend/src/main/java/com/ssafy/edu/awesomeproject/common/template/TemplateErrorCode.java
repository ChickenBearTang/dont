package com.ssafy.edu.awesomeproject.common.template;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum TemplateErrorCode implements ErrorCode {
    TEMPLATE_BAD_REQUEST(HttpStatus.BAD_REQUEST, "TEMPLATE_400_1", "Template bad request example."),
    TEMPLATE_NOT_FOUND(
            HttpStatus.NOT_FOUND, "TEMPLATE_404_1", "Template resource not found example."),
    TEMPLATE_CONFLICT(HttpStatus.CONFLICT, "TEMPLATE_409_1", "Template conflict example."),
    TEMPLATE_INTERNAL_SERVER_ERROR(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "TEMPLATE_500_1",
            "Template internal server error example.");

    private final HttpStatus status;
    private final String code;
    private final String message;

    TemplateErrorCode(HttpStatus status, String code, String message) {
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
