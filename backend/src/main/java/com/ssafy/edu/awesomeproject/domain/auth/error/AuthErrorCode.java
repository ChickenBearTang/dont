package com.ssafy.edu.awesomeproject.domain.auth.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum AuthErrorCode implements ErrorCode {
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "AUTH_400_1", "잘못된 입력입니다."),
    EMAIL_ALREADY_EXISTS(HttpStatus.CONFLICT, "AUTH_409_1", "이미 사용 중인 이메일입니다."),
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "AUTH_401_1", "인증이 필요합니다."),
    BAD_CREDENTIALS(HttpStatus.UNAUTHORIZED, "AUTH_401_2", "잘못된 자격 증명입니다."),
    REFRESH_TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "AUTH_401_3", "리프레시 토큰이 만료되었습니다."),
    REFRESH_TOKEN_INVALID(HttpStatus.UNAUTHORIZED, "AUTH_401_4", "리프레시 토큰이 유효하지 않습니다."),
    FORBIDDEN(HttpStatus.FORBIDDEN, "AUTH_403_1", "접근이 거부되었습니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

    AuthErrorCode(HttpStatus httpStatus, String code, String message){
        this.httpStatus = httpStatus;
        this.code = code;
        this.message = message;
    }

    @Override
    public HttpStatus status(){
        return httpStatus;
    }

    @Override
    public String code(){
        return code;
    }

    @Override
    public String message(){
        return message;
    }


}
