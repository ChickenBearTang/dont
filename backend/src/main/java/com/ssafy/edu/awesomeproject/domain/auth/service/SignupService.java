package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;

@Service
public class SignupService {
    private static final List<String> NICKNAME_PREFIXES =
            List.of("알뜰한", "든든한", "차분한", "영리한", "기민한", "반듯한");
    private static final List<String> NICKNAME_SUFFIXES =
            List.of("펭귄", "곰", "다람쥐", "여우", "고래", "토끼");
    private static final int NICKNAME_MAX_ATTEMPTS = 20;

    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final CohortRepository cohortRepository;
    private final EmailVerificationService emailVerificationService;
    private final DefaultProfileImagePolicy defaultProfileImagePolicy;

    public SignupService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            CohortRepository cohortRepository,
            EmailVerificationService emailVerificationService,
            DefaultProfileImagePolicy defaultProfileImagePolicy) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.cohortRepository = cohortRepository;
        this.emailVerificationService = emailVerificationService;
        this.defaultProfileImagePolicy = defaultProfileImagePolicy;
    }

    public void signup(
            String email,
            String rawPassword,
            String name,
            LocalDate birthDate,
            boolean termsAgreed,
            Long cohortId) {

        String normalizedEmail = email.trim().toLowerCase(Locale.ROOT);

        if (userRepository.existsByEmail(normalizedEmail)) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }
        emailVerificationService.assertVerified(normalizedEmail);

        Cohort cohort =
                cohortRepository
                        .findById(cohortId)
                        .orElseThrow(() -> new AuthException(CommunityErrorCode.COHORT_NOT_FOUND));

        String encodedPassword = passwordHashService.encode(rawPassword);
        LocalDateTime termsAgreedAt = termsAgreed ? LocalDateTime.now() : null;
        String generatedNickname = generateUniqueNickname();
        String defaultProfileImageKey = defaultProfileImagePolicy.pickRandomKey();
        User user =
                new User(
                        normalizedEmail,
                        encodedPassword,
                        name,
                        birthDate,
                        generatedNickname,
                        defaultProfileImageKey,
                        termsAgreed,
                        termsAgreedAt,
                        UserRole.USER,
                        cohort);
        try {
            userRepository.save(user);
            emailVerificationService.clearVerified(normalizedEmail);
        } catch (DataIntegrityViolationException ex) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }
    }

    private String generateUniqueNickname() {
        for (int attempt = 0; attempt < NICKNAME_MAX_ATTEMPTS; attempt++) {
            String nickname = generateNicknameCandidate();
            if (!userRepository.existsByNickname(nickname)) {
                return nickname;
            }
        }

        throw new AuthException(AuthErrorCode.AUTHENTICATION_FAILED);
    }

    private String generateNicknameCandidate() {
        String prefix =
                NICKNAME_PREFIXES.get(
                        ThreadLocalRandom.current().nextInt(NICKNAME_PREFIXES.size()));
        String suffix =
                NICKNAME_SUFFIXES.get(
                        ThreadLocalRandom.current().nextInt(NICKNAME_SUFFIXES.size()));
        int number = ThreadLocalRandom.current().nextInt(100, 1000);
        return prefix + suffix + number;
    }
}
