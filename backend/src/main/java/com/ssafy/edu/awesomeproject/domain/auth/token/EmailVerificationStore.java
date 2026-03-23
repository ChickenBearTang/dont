package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.time.Duration;
import java.util.Optional;

public interface EmailVerificationStore {
    void saveCode(String email, String code, Duration timeToLive);

    Optional<String> findCode(String email);

    void removeCode(String email);

    void markVerified(String email, Duration timeToLive);

    boolean isVerified(String email);

    void clearVerified(String email);
}
