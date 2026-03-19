package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import java.util.Locale;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class LoginService {
    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final AuthTokenService authTokenService;

    public LoginService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            AuthTokenService authTokenService) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.authTokenService = authTokenService;
    }

    public LoginResult login(String email, String password) {
        String normalizedEmail = normalizeEmail(email);

        User user =
                userRepository
                        .findByEmail(normalizedEmail)
                        .orElseThrow(() -> new AuthException(AuthErrorCode.BAD_CREDENTIALS));

        if (!passwordHashService.matches(password, user.getPassword())) {
            throw new AuthException(AuthErrorCode.BAD_CREDENTIALS);
        }

        AuthTokenService.LoginTokenResult loginTokenResult =
                authTokenService.issueLoginTokens(user);

        return new LoginResult(
                user.getId(),
                user.getEmail(),
                user.getUserRole(),
                loginTokenResult.accessToken(),
                loginTokenResult.tokenType(),
                loginTokenResult.expiresInSeconds(),
                loginTokenResult.refreshToken(),
                loginTokenResult.refreshTokenExpiresInSeconds());
    }

    private String normalizeEmail(String email) {
        return email.trim().toLowerCase(Locale.ROOT);
    }

    public record LoginResult(
            Long userId,
            String email,
            String userRole,
            String accessToken,
            String tokenType,
            long expiresInSeconds,
            String refreshToken,
            long refreshTokenExpiresInSeconds) {}
}
