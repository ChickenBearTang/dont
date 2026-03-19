package com.ssafy.edu.awesomeproject.domain.fin.account.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum AccountErrorCode implements ErrorCode {
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "ACC_400_1", "잘못된 입력입니다."),
    ACCOUNT_NOT_FOUND(HttpStatus.NOT_FOUND, "ACC_404_1", "계좌를 찾을 수 없습니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "ACC_404_2", "사용자를 찾을 수 없습니다."),
    SAVINGS_SETTING_NOT_FOUND(
            HttpStatus.NOT_FOUND, "ACC_404_3", "활성화된 저축 설정이 없습니다. 먼저 설정을 완료해 주세요."),
    PRIMARY_ACCOUNT_NOT_FOUND(HttpStatus.NOT_FOUND, "ACC_404_4", "주계좌를 찾을 수 없습니다."),
    SAVEBOX_ACCOUNT_NOT_FOUND(HttpStatus.NOT_FOUND, "ACC_404_5", "세이브박스 계좌을 찾을 수 없습니다."),
    FINANCE_USER_KEY_NOT_FOUND(
            HttpStatus.BAD_REQUEST, "ACC_400_2", "사용자의 Finance User Key가 설정되지 않았습니다."),
    API_RESPONSE_ERROR(
            HttpStatus.INTERNAL_SERVER_ERROR, "ACC_500_1", "금융 API 응답이 올바르지 않거나 처리에 실패했습니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

    AccountErrorCode(HttpStatus httpStatus, String code, String message) {
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
