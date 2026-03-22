package com.ssafy.edu.awesomeproject.domain.user.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum UserErrorCode implements ErrorCode {
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "USER_404_1", "사용자를 찾을 수 없습니다."),
    NICKNAME_INVALID_LENGTH(HttpStatus.BAD_REQUEST, "USER_400_1", "닉네임은 2자 이상 20자 이하여야 합니다."),
    NICKNAME_INVALID_FORMAT(
            HttpStatus.BAD_REQUEST, "USER_400_2", "닉네임은 한글, 영문, 숫자, 밑줄(_)만 사용할 수 있습니다."),
    NICKNAME_ALREADY_EXISTS(HttpStatus.CONFLICT, "USER_409_1", "이미 사용 중인 닉네임입니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

    UserErrorCode(HttpStatus httpStatus, String code, String message) {
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
