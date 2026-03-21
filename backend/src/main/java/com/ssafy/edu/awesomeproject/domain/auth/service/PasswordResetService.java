package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
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
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PasswordResetService {
    private static final int RESET_CODE_LENGTH = 6;
    private static final Duration RESET_CODE_TTL = Duration.ofMinutes(10);

    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final PasswordResetTokenStore passwordResetTokenStore;
    private final PasswordResetEmailSender passwordResetEmailSender;
    private final RefreshTokenStore refreshTokenStore;

    public PasswordResetService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            PasswordResetTokenStore passwordResetTokenStore,
            PasswordResetEmailSender passwordResetEmailSender,
            RefreshTokenStore refreshTokenStore) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.passwordResetTokenStore = passwordResetTokenStore;
        this.passwordResetEmailSender = passwordResetEmailSender;
        this.refreshTokenStore = refreshTokenStore;
    }

    public RequestResult requestReset(String email) {
        String normalizedEmail = normalizeEmail(email);

        userRepository
                .findByEmail(normalizedEmail)
                .ifPresent(
                        user -> {
                            String code = generateCode();
                            passwordResetTokenStore.saveCode(
                                    normalizedEmail, code, RESET_CODE_TTL);
                            try {
                                passwordResetEmailSender.sendResetCode(
                                        normalizedEmail, code, RESET_CODE_TTL);
                            } catch (RuntimeException exception) {
                                passwordResetTokenStore.removeCode(normalizedEmail);
                                throw exception;
                            }
                        });

        // 계정 존재 여부를 노출하지 않기 위해 동일 응답을 반환한다.
        return new RequestResult(
                "입력한 이메일로 비밀번호 재설정 안내를 전송했습니다.", RESET_CODE_TTL.getSeconds());
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
            throw new AuthException(AuthErrorCode.PASSWORD_RESET_CODE_INVALID);
        }

        User user =
                userRepository
                        .findByEmail(normalizedEmail)
                        .orElseThrow(
                                () -> new AuthException(AuthErrorCode.PASSWORD_RESET_CODE_INVALID));

        user.changePassword(passwordHashService.encode(newPassword));
        passwordResetTokenStore.removeCode(normalizedEmail);
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
