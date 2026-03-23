package com.ssafy.edu.awesomeproject.domain.auth.token;

import com.ssafy.edu.awesomeproject.domain.auth.service.AuthCodePurpose;
import java.time.Duration;

public interface AuthCodeAttemptStore {
    long incrementSendAttempts(AuthCodePurpose purpose, String email, Duration timeToLive);

    long incrementVerifyAttempts(AuthCodePurpose purpose, String email, Duration timeToLive);

    void clearVerifyAttempts(AuthCodePurpose purpose, String email);
}
