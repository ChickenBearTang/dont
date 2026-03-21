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
    private static final List<String> DEFAULT_PROFILE_IMAGE_KEYS =
            List.of(
                    "public/profile/default/profile_penguin.png",
                    "public/profile/default/profile_bear.png");
    private static final int NICKNAME_MAX_ATTEMPTS = 20;

    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final CohortRepository cohortRepository;
    private final EmailVerificationService emailVerificationService;

    public SignupService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            CohortRepository cohortRepository,
            EmailVerificationService emailVerificationService) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.cohortRepository = cohortRepository;
        this.emailVerificationService = emailVerificationService;
    }

    public void signup(
            String email,
            String rawPassword,
            String name,
            LocalDate birthDate,
            boolean termsAgreed,
            Long cohortId) {
        // TODO : 회원가입시에는 소문자로 저장, 로그인시에는 대소문자 구분없이 저장, 이 부분 해결해야함.
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
        String defaultProfileImageKey = pickDefaultProfileImageKey();
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

    private String pickDefaultProfileImageKey() {
        int index = ThreadLocalRandom.current().nextInt(DEFAULT_PROFILE_IMAGE_KEYS.size());
        return DEFAULT_PROFILE_IMAGE_KEYS.get(index);
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
