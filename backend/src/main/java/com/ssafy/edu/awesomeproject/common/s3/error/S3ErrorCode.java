package com.ssafy.edu.awesomeproject.common.s3.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum S3ErrorCode implements ErrorCode {
    INVALID_CONTENT_TYPE(HttpStatus.BAD_REQUEST, "S3_400_1", "지원하지 않는 파일 형식입니다."),
    INVALID_FILE_NAME(HttpStatus.BAD_REQUEST, "S3_400_2", "파일명이 유효하지 않습니다."),
    INVALID_OBJECT_KEY(HttpStatus.BAD_REQUEST, "S3_400_3", "파일 key가 유효하지 않습니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

    S3ErrorCode(HttpStatus httpStatus, String code, String message) {
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
