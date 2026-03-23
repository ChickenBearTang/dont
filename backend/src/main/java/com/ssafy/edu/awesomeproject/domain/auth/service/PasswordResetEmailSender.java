package com.ssafy.edu.awesomeproject.domain.auth.service;

import java.time.Duration;

public interface PasswordResetEmailSender {
    void sendResetCode(String email, String code, Duration timeToLive);
}
