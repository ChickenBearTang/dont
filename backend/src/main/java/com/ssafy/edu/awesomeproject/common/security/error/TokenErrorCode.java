package com.ssafy.edu.awesomeproject.common.security.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum TokenErrorCode implements ErrorCode {
    TOKEN_INVALID(HttpStatus.UNAUTHORIZED, "TOKEN_401_1", "유효하지 않은 토큰입니다."),
    TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "TOKEN_401_2", "토큰이 만료되었습니다."),
    ACCESS_TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "TOKEN_401_6", "액세스 토큰이 만료되었습니다."),
    REFRESH_TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "TOKEN_401_7", "리프레시 토큰이 만료되었습니다."),
    INVALID_TOKEN_SIGNATURE(HttpStatus.UNAUTHORIZED, "TOKEN_401_8", "토큰 서명이 유효하지 않습니다."),
    TOKEN_TYPE_MISMATCH(HttpStatus.UNAUTHORIZED, "TOKEN_401_3", "토큰 타입이 올바르지 않습니다."),
    TOKEN_SESSION_INVALID(HttpStatus.UNAUTHORIZED, "TOKEN_401_4", "세션 정보가 올바르지 않습니다."),
    TOKEN_BLACKLISTED(HttpStatus.UNAUTHORIZED, "TOKEN_401_5", "차단된 토큰입니다.");

    private final HttpStatus status;
    private final String code;
    private final String message;

    TokenErrorCode(HttpStatus status, String code, String message) {
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
