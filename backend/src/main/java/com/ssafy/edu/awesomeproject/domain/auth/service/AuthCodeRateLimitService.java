package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.token.AuthCodeAttemptStore;
import java.time.Duration;
import java.util.EnumMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class AuthCodeRateLimitService {
    private final AuthCodeAttemptStore authCodeAttemptStore;
    private final Map<AuthCodePurpose, RateLimitPolicy> policies;

    public AuthCodeRateLimitService(
            AuthCodeAttemptStore authCodeAttemptStore,
            @Value("${auth.email-verification.send-limit-window-seconds}")
                    long emailVerificationSendLimitWindowSeconds,
            @Value("${auth.email-verification.max-send-attempts}")
                    int emailVerificationMaxSendAttempts,
            @Value("${auth.email-verification.verify-attempt-window-seconds}")
                    long emailVerificationVerifyAttemptWindowSeconds,
            @Value("${auth.email-verification.max-verify-attempts}")
                    int emailVerificationMaxVerifyAttempts,
            @Value("${auth.password-reset.send-limit-window-seconds}")
                    long passwordResetSendLimitWindowSeconds,
            @Value("${auth.password-reset.max-send-attempts}") int passwordResetMaxSendAttempts,
            @Value("${auth.password-reset.verify-attempt-window-seconds}")
                    long passwordResetVerifyAttemptWindowSeconds,
            @Value("${auth.password-reset.max-verify-attempts}")
                    int passwordResetMaxVerifyAttempts) {
        this.authCodeAttemptStore = authCodeAttemptStore;
        this.policies = new EnumMap<>(AuthCodePurpose.class);
        policies.put(
                AuthCodePurpose.EMAIL_VERIFICATION,
                new RateLimitPolicy(
                        Duration.ofSeconds(emailVerificationSendLimitWindowSeconds),
                        emailVerificationMaxSendAttempts,
                        Duration.ofSeconds(emailVerificationVerifyAttemptWindowSeconds),
                        emailVerificationMaxVerifyAttempts));
        policies.put(
                AuthCodePurpose.PASSWORD_RESET,
                new RateLimitPolicy(
                        Duration.ofSeconds(passwordResetSendLimitWindowSeconds),
                        passwordResetMaxSendAttempts,
                        Duration.ofSeconds(passwordResetVerifyAttemptWindowSeconds),
                        passwordResetMaxVerifyAttempts));
    }

    public void checkSendLimit(AuthCodePurpose purpose, String email) {
        RateLimitPolicy policy = policies.get(purpose);
        long sendAttempts =
                authCodeAttemptStore.incrementSendAttempts(purpose, email, policy.sendWindow());
        if (sendAttempts > policy.maxSendAttempts()) {
            throw new AuthException(purpose.sendLimitErrorCode());
        }
    }

    public boolean registerVerificationFailure(AuthCodePurpose purpose, String email) {
        RateLimitPolicy policy = policies.get(purpose);
        long verifyAttempts =
                authCodeAttemptStore.incrementVerifyAttempts(purpose, email, policy.verifyWindow());
        return verifyAttempts >= policy.maxVerifyAttempts();
    }

    public void clearVerificationFailures(AuthCodePurpose purpose, String email) {
        authCodeAttemptStore.clearVerifyAttempts(purpose, email);
    }

    private record RateLimitPolicy(
            Duration sendWindow,
            int maxSendAttempts,
            Duration verifyWindow,
            int maxVerifyAttempts) {}
}
