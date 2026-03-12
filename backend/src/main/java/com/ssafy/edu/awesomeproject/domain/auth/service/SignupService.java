package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import java.util.Locale;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class SignupService {
    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;

    public SignupService(UserRepository userRepository, PasswordHashService passwordHashService) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
    }

    public SignupResult signup(String email, String rawPassword) {
        // TODO : 회원가입시에는 소문자로 저장, 로그인시에는 대소문자 구분없이 저장, 이 부분 해결해야함.
        String normalizedEmail = email.trim().toLowerCase(Locale.ROOT);

        if (userRepository.existsByEmail(normalizedEmail)) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }

        String encodedPassword = passwordHashService.encode(rawPassword);
        User user = new User(normalizedEmail, encodedPassword, null, null, null, UserRole.USER);
        User savedUser;

        try {
            savedUser = userRepository.save(user);
        } catch (DataIntegrityViolationException ex) {
            throw new AuthException(AuthErrorCode.EMAIL_ALREADY_EXISTS);
        }

        return new SignupResult(savedUser.getId(), savedUser.getEmail(), savedUser.getUserRole());
    }

    public record SignupResult(Long userId, String email, String userRole) {}
}
