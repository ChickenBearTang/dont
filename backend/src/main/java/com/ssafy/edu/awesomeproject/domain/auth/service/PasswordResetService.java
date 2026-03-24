package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserStatus;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.token.PasswordResetTokenStore;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.Locale;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PasswordResetService {
    private static final int RESET_CODE_LENGTH = 6;

    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final PasswordResetTokenStore passwordResetTokenStore;
    private final PasswordResetEmailSender passwordResetEmailSender;
    private final RefreshTokenStore refreshTokenStore;
    private final AuthCodeRateLimitService authCodeRateLimitService;
    private final Duration resetCodeTimeToLive;

    public PasswordResetService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            PasswordResetTokenStore passwordResetTokenStore,
            PasswordResetEmailSender passwordResetEmailSender,
            RefreshTokenStore refreshTokenStore,
            AuthCodeRateLimitService authCodeRateLimitService,
            @Value("${auth.password-reset.code-ttl-seconds}") long resetCodeTtlSeconds) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.passwordResetTokenStore = passwordResetTokenStore;
        this.passwordResetEmailSender = passwordResetEmailSender;
        this.refreshTokenStore = refreshTokenStore;
        this.authCodeRateLimitService = authCodeRateLimitService;
        this.resetCodeTimeToLive = Duration.ofSeconds(resetCodeTtlSeconds);
    }

    public RequestResult requestReset(String email) {
        String normalizedEmail = normalizeEmail(email);

        authCodeRateLimitService.checkSendLimit(AuthCodePurpose.PASSWORD_RESET, normalizedEmail);

        userRepository
                .findByEmailAndStatus(normalizedEmail, UserStatus.ACTIVE)
                .ifPresent(
                        user -> {
                            String code = generateCode();
                            passwordResetTokenStore.saveCode(
                                    normalizedEmail, code, resetCodeTimeToLive);
                            authCodeRateLimitService.clearVerificationFailures(
                                    AuthCodePurpose.PASSWORD_RESET, normalizedEmail);
                            try {
                                passwordResetEmailSender.sendResetCode(
                                        normalizedEmail, code, resetCodeTimeToLive);
                            } catch (RuntimeException exception) {
                                passwordResetTokenStore.removeCode(normalizedEmail);
                                throw exception;
                            }
                        });

        return new RequestResult("입력한 이메일로 비밀번호 재설정 코드를 전송했습니다.", resetCodeTimeToLive.getSeconds());
    }

    @Transactional
    public ConfirmResult confirmReset(String email, String code, String newPassword) {
        String normalizedEmail = normalizeEmail(email);
        String normalizedCode = code.trim();

        String savedCode =
                passwordResetTokenStore
                        .findCode(normalizedEmail)
                        .orElseThrow(
                                () -> new AuthException(AuthErrorCode.PASSWORD_RESET_CODE_EXPIRED));

        if (!MessageDigest.isEqual(
                savedCode.getBytes(StandardCharsets.UTF_8),
                normalizedCode.getBytes(StandardCharsets.UTF_8))) {
            boolean limitExceeded =
                    authCodeRateLimitService.registerVerificationFailure(
                            AuthCodePurpose.PASSWORD_RESET, normalizedEmail);
            if (limitExceeded) {
                passwordResetTokenStore.removeCode(normalizedEmail);
                throw new AuthException(AuthErrorCode.PASSWORD_RESET_ATTEMPTS_EXCEEDED);
            }
            throw new AuthException(AuthErrorCode.PASSWORD_RESET_CODE_INVALID);
        }

        User user =
                userRepository
                        .findActiveByEmail(normalizedEmail)
                        .orElseThrow(
                                () -> new AuthException(AuthErrorCode.PASSWORD_RESET_CODE_INVALID));

        user.changePassword(passwordHashService.encode(newPassword));
        passwordResetTokenStore.removeCode(normalizedEmail);
        authCodeRateLimitService.clearVerificationFailures(
                AuthCodePurpose.PASSWORD_RESET, normalizedEmail);
        refreshTokenStore.deleteByUserId(user.getId());

        return new ConfirmResult(true);
    }

    private String normalizeEmail(String email) {
        return email.trim().toLowerCase(Locale.ROOT);
    }

    private String generateCode() {
        int bound = (int) Math.pow(10, RESET_CODE_LENGTH);
        return String.format(
                "%0" + RESET_CODE_LENGTH + "d", ThreadLocalRandom.current().nextInt(bound));
    }

    public record RequestResult(String message, long expiresInSeconds) {}

    public record ConfirmResult(boolean resetCompleted) {}
}
