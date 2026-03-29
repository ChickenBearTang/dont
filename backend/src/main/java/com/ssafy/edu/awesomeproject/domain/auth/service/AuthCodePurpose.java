package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;

public enum AuthCodePurpose {
    EMAIL_VERIFICATION(
            "email-verification",
            AuthErrorCode.EMAIL_VERIFICATION_SEND_LIMIT_EXCEEDED,
            AuthErrorCode.EMAIL_VERIFICATION_ATTEMPTS_EXCEEDED),
    PASSWORD_RESET(
            "password-reset",
            AuthErrorCode.PASSWORD_RESET_SEND_LIMIT_EXCEEDED,
            AuthErrorCode.PASSWORD_RESET_ATTEMPTS_EXCEEDED);

    private final String key;
    private final AuthErrorCode sendLimitErrorCode;
    private final AuthErrorCode verifyLimitErrorCode;

    AuthCodePurpose(
            String key, AuthErrorCode sendLimitErrorCode, AuthErrorCode verifyLimitErrorCode) {
        this.key = key;
        this.sendLimitErrorCode = sendLimitErrorCode;
        this.verifyLimitErrorCode = verifyLimitErrorCode;
    }

    public String key() {
        return key;
    }

    public AuthErrorCode sendLimitErrorCode() {
        return sendLimitErrorCode;
    }

    public AuthErrorCode verifyLimitErrorCode() {
        return verifyLimitErrorCode;
    }
}
