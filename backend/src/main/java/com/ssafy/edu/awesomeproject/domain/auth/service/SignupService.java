package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import java.util.Locale;

import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class SignupService {
    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final CohortRepository cohortRepository;

    public SignupService(UserRepository userRepository,
                         PasswordHashService passwordHashService,
                         CohortRepository cohortRepository) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.cohortRepository = cohortRepository;
    }

    public SignupResult signup(String email, String rawPassword, Integer generationNo) {
        // TODO : 회원가입시에는 소문자로 저장, 로그인시에는 대소문자 구분없이 저장, 이 부분 해결해야함.
        String normalizedEmail = email.trim().toLowerCase(Locale.ROOT);

        if (userRepository.existsByEmail(normalizedEmail)) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }

        Cohort cohort = cohortRepository.findByGenerationNo(generationNo)
            .orElseThrow(() -> new AuthException(CommunityErrorCode.COHORT_NOT_FOUND));

        String encodedPassword = passwordHashService.encode(rawPassword);
        User user = new User(normalizedEmail, encodedPassword, null, null, null, UserRole.USER, cohort);
        User savedUser;

        try {
            savedUser = userRepository.save(user);
        } catch (DataIntegrityViolationException ex) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }

        return new SignupResult(
            savedUser.getId(),
            savedUser.getEmail(),
            savedUser.getUserRole(),
            savedUser.getCohort() != null ? savedUser.getCohort().getGenerationNo() : null);
    }

    public record SignupResult(Long userId, String email, String userRole, Integer generationNo) {}
}
