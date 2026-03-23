package com.ssafy.edu.awesomeproject.domain.user.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum UserErrorCode implements ErrorCode {
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "USER_404_1", "사용자를 찾을 수 없습니다."),
    NICKNAME_INVALID_LENGTH(HttpStatus.BAD_REQUEST, "USER_400_1", "닉네임은 2자 이상 20자 이하여야 합니다."),
    NICKNAME_INVALID_FORMAT(
            HttpStatus.BAD_REQUEST, "USER_400_2", "닉네임은 한글, 영문, 숫자, 밑줄(_)만 사용할 수 있습니다."),
    MY_PAGE_UPDATE_EMPTY(HttpStatus.BAD_REQUEST, "USER_400_3", "수정할 마이페이지 항목이 없습니다."),
    NAME_INVALID(HttpStatus.BAD_REQUEST, "USER_400_4", "이름은 공백일 수 없습니다."),
    NEW_PASSWORD_SAME_AS_CURRENT(HttpStatus.BAD_REQUEST, "USER_400_5", "새 비밀번호는 현재 비밀번호와 달라야 합니다."),
    CURRENT_PASSWORD_MISMATCH(HttpStatus.UNAUTHORIZED, "USER_401_1", "현재 비밀번호가 일치하지 않습니다."),
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
