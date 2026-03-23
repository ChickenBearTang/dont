package com.ssafy.edu.awesomeproject.domain.auth.service;

import java.time.Duration;

public interface VerificationEmailSender {
    void sendVerificationCode(String email, String code, Duration timeToLive);
}
