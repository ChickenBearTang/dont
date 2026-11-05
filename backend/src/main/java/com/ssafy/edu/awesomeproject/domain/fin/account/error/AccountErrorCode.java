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
    INSUFFICIENT_BALANCE(HttpStatus.BAD_REQUEST, "ACC_400_3", "계좌 잔액이 부족합니다."),
    INVALID_AMOUNT(HttpStatus.BAD_REQUEST, "ACC_400_4", "금액은 1원 이상의 정수여야 합니다."),
    SAME_ACCOUNT_TRANSFER(HttpStatus.BAD_REQUEST, "ACC_400_5", "같은 계좌로는 이체할 수 없습니다."),
    TRANSFER_LIMIT_EXCEEDED(HttpStatus.BAD_REQUEST, "ACC_400_6", "1회 이체 한도를 넘었습니다."),
    NOT_A_DEPOSIT_ACCOUNT(
            HttpStatus.BAD_REQUEST, "ACC_400_7", "입출금 계좌에만 입금할 수 있습니다. 세이브박스에는 이체로 넣어 주세요."),
    ACCOUNT_NOT_ACTIVE(HttpStatus.CONFLICT, "ACC_409_2", "사용할 수 없는 상태의 계좌입니다."),
    SAVEBOX_ALREADY_EXISTS(HttpStatus.CONFLICT, "ACC_409_3", "이미 세이브박스가 있습니다."),
    MOCK_DATA_DISABLED(
            HttpStatus.FORBIDDEN, "ACC_403_1", "모의 입금·카드 등록은 개발·시연 환경에서만 사용할 수 있습니다."),
    ACCOUNT_NO_EXHAUSTED(
            HttpStatus.INTERNAL_SERVER_ERROR, "ACC_500_2", "새 계좌번호를 만들 수 없습니다. 잠시 뒤 다시 시도해 주세요.");

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
