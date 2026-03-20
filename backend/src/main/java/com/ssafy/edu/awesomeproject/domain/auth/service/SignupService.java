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
import java.util.Locale;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;

@Service
public class SignupService {
    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final CohortRepository cohortRepository;

    public SignupService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            CohortRepository cohortRepository) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.cohortRepository = cohortRepository;
    }

    public void signup(
            String email,
            String rawPassword,
            String name,
            LocalDate birthDate,
            String nickname,
            boolean termsAgreed,
            Long cohortId) {
        String normalizedEmail = email.trim().toLowerCase(Locale.ROOT);

        if (userRepository.existsByEmail(normalizedEmail)) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }

        Cohort cohort =
                cohortRepository
                        .findById(cohortId)
                        .orElseThrow(() -> new AuthException(CommunityErrorCode.COHORT_NOT_FOUND));

        String encodedPassword = passwordHashService.encode(rawPassword);
        LocalDateTime termsAgreedAt = termsAgreed ? LocalDateTime.now() : null;
        User user =
                new User(
                        normalizedEmail,
                        encodedPassword,
                        name,
                        birthDate,
                        nickname,
                        null,
                        termsAgreed,
                        termsAgreedAt,
                        UserRole.USER,
                        cohort);
        try {
            userRepository.save(user);
        } catch (DataIntegrityViolationException ex) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }
    }
}
