package com.ssafy.edu.awesomeproject.domain.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class LoginServiceTest {

    @Mock private UserRepository userRepository;
    @Mock private PasswordHashService passwordHashService;
    @Mock private AuthTokenService authTokenService;

    private LoginService loginService;

    @BeforeEach
    void setUp() {
        loginService = new LoginService(userRepository, passwordHashService, authTokenService);
    }

    @Test
    void loginWithNullEmailFailsClosedBeforeRepositoryLookup() {
        assertBadCredentialsAndNoRepositoryLookup(null, "Password123!");
    }

    @Test
    void loginWithBlankEmailFailsClosedBeforeRepositoryLookup() {
        assertBadCredentialsAndNoRepositoryLookup("   ", "Password123!");
    }

    @Test
    void loginWithNullPasswordFailsClosedBeforeRepositoryLookup() {
        assertBadCredentialsAndNoRepositoryLookup("user@example.com", null);
    }

    @Test
    void loginWithBlankPasswordFailsClosedBeforeRepositoryLookup() {
        assertBadCredentialsAndNoRepositoryLookup("user@example.com", "\t\n ");
    }

    private void assertBadCredentialsAndNoRepositoryLookup(String email, String password) {
        assertThatThrownBy(() -> loginService.login(email, password))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.BAD_CREDENTIALS));

        verify(userRepository, never()).findByEmail(any());
        verifyNoInteractions(passwordHashService, authTokenService);
    }
}
