package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.token.EmailVerificationStore;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.Locale;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class EmailVerificationService {
    private static final int VERIFICATION_CODE_LENGTH = 6;

    private final UserRepository userRepository;
    private final EmailVerificationStore emailVerificationStore;
    private final VerificationEmailSender verificationEmailSender;
    private final Duration codeTimeToLive;
    private final Duration verifiedTimeToLive;

    public EmailVerificationService(
            UserRepository userRepository,
            EmailVerificationStore emailVerificationStore,
            VerificationEmailSender verificationEmailSender,
            @Value("${auth.email-verification.code-ttl-seconds}") long codeTtlSeconds,
            @Value("${auth.email-verification.verified-ttl-seconds}") long verifiedTtlSeconds) {
        this.userRepository = userRepository;
        this.emailVerificationStore = emailVerificationStore;
        this.verificationEmailSender = verificationEmailSender;
        this.codeTimeToLive = Duration.ofSeconds(codeTtlSeconds);
        this.verifiedTimeToLive = Duration.ofSeconds(verifiedTtlSeconds);
    }

    public SendResult sendVerificationCode(String email) {
        String normalizedEmail = normalizeEmail(email);

        if (userRepository.existsByEmail(normalizedEmail)) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }

        String code = generateCode();
        emailVerificationStore.saveCode(normalizedEmail, code, codeTimeToLive);
        emailVerificationStore.clearVerified(normalizedEmail);
        try {
            verificationEmailSender.sendVerificationCode(normalizedEmail, code, codeTimeToLive);
        } catch (RuntimeException exception) {
            emailVerificationStore.removeCode(normalizedEmail);
            throw exception;
        }

        return new SendResult(normalizedEmail, codeTimeToLive.getSeconds());
    }

    public VerifyResult verifyCode(String email, String code) {
        String normalizedEmail = normalizeEmail(email);
        String normalizedCode = code.trim();

        String savedCode =
                emailVerificationStore
                        .findCode(normalizedEmail)
                        .orElseThrow(
                                () ->
                                        new AuthException(
                                                AuthErrorCode.EMAIL_VERIFICATION_CODE_EXPIRED));

        if (!MessageDigest.isEqual(
                savedCode.getBytes(StandardCharsets.UTF_8),
                normalizedCode.getBytes(StandardCharsets.UTF_8))) {
            throw new AuthException(AuthErrorCode.EMAIL_VERIFICATION_CODE_INVALID);
        }

        emailVerificationStore.removeCode(normalizedEmail);
        emailVerificationStore.markVerified(normalizedEmail, verifiedTimeToLive);

        return new VerifyResult(normalizedEmail, true, verifiedTimeToLive.getSeconds());
    }

    public void assertVerified(String email) {
        String normalizedEmail = normalizeEmail(email);
        if (!emailVerificationStore.isVerified(normalizedEmail)) {
            throw new AuthException(AuthErrorCode.EMAIL_NOT_VERIFIED);
        }
    }

    public void clearVerified(String email) {
        emailVerificationStore.clearVerified(normalizeEmail(email));
    }

    private String normalizeEmail(String email) {
        return email.trim().toLowerCase(Locale.ROOT);
    }

    private String generateCode() {
        int bound = (int) Math.pow(10, VERIFICATION_CODE_LENGTH);
        return String.format(
                "%0" + VERIFICATION_CODE_LENGTH + "d", ThreadLocalRandom.current().nextInt(bound));
    }

    public record SendResult(String email, long expiresInSeconds) {}

    public record VerifyResult(String email, boolean verified, long verifiedExpiresInSeconds) {}
}
