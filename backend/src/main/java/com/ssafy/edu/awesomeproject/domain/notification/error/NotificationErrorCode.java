package com.ssafy.edu.awesomeproject.domain.notification.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum NotificationErrorCode implements ErrorCode {
    NOTIFICATION_NOT_FOUND(HttpStatus.NOT_FOUND, "NOTI_404_1", "알림을 찾을 수 없습니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "NOTI_404_2", "사용자를 찾을 수 없습니다."),
    INVALID_NOTIFICATION_REQUEST(HttpStatus.BAD_REQUEST, "NOTI_400_1", "잘못된 알림 요청입니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

    NotificationErrorCode(HttpStatus httpStatus, String code, String message) {
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
