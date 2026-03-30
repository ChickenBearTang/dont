package com.ssafy.edu.awesomeproject.common.template;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum TemplateErrorCode implements ErrorCode {
    TEMPLATE_BAD_REQUEST(HttpStatus.BAD_REQUEST, "TEMPLATE_400_1", "템플릿 잘못된 요청 예시입니다."),
    TEMPLATE_NOT_FOUND(
            HttpStatus.NOT_FOUND, "TEMPLATE_404_1", "템플릿 리소스를 찾을 수 없는 예시입니다."),
    TEMPLATE_CONFLICT(HttpStatus.CONFLICT, "TEMPLATE_409_1", "템플릿 충돌 예시입니다."),
    TEMPLATE_INTERNAL_SERVER_ERROR(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "TEMPLATE_500_1",
            "템플릿 서버 내부 오류 예시입니다.");

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
