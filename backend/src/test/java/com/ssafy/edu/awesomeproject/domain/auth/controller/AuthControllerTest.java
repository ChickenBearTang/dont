package com.ssafy.edu.awesomeproject.domain.auth.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.domain.auth.cookie.RefreshTokenCookieService;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.LoginRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.service.AuthRateLimitService;
import com.ssafy.edu.awesomeproject.domain.auth.service.AuthTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.service.LoginService;
import com.ssafy.edu.awesomeproject.domain.auth.service.SignupService;
import java.time.Duration;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

@ExtendWith(MockitoExtension.class)
class AuthControllerTest {

    @Mock private LoginService loginService;
    @Mock private SignupService signupService;
    @Mock private AuthTokenService authTokenService;
    @Mock private AuthRateLimitService authRateLimitService;
    @Mock private RefreshTokenCookieService refreshTokenCookieService;

    private AuthController authController;

    @BeforeEach
    void setUp() {
        authController =
                new AuthController(
                        loginService,
                        signupService,
                        authTokenService,
                        authRateLimitService,
                        refreshTokenCookieService);
    }

    @Test
    void loginRejectsWhenRateLimitExceeded() {
        LoginRequestDto requestDto = new LoginRequestDto("user@example.com", "password123");
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        when(authRateLimitService.resolveClientIp(request)).thenReturn("127.0.0.1");
        AuthException expected = new AuthException(AuthErrorCode.TOO_MANY_REQUESTS);
        org.mockito.Mockito.doThrow(expected)
                .when(authRateLimitService)
                .validateLoginAllowed("user@example.com", "127.0.0.1");

        assertThatThrownBy(() -> authController.login(requestDto, request, response))
                .isSameAs(expected);

        verify(loginService, never()).login(any(), any());
    }

    @Test
    void loginBadCredentialsAreCountedForRateLimit() {
        LoginRequestDto requestDto = new LoginRequestDto("user@example.com", "password123");
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        when(authRateLimitService.resolveClientIp(request)).thenReturn("127.0.0.1");
        AuthException badCredentials = new AuthException(AuthErrorCode.BAD_CREDENTIALS);
        when(loginService.login("user@example.com", "password123")).thenThrow(badCredentials);

        assertThatThrownBy(() -> authController.login(requestDto, request, response))
                .isSameAs(badCredentials);

        verify(authRateLimitService).recordLoginFailure("user@example.com", "127.0.0.1");
        verify(authRateLimitService, never()).resetLoginFailures(any());
    }

    @Test
    void loginSuccessResetsEmailRateLimitBucket() {
        LoginRequestDto requestDto = new LoginRequestDto("user@example.com", "password123");
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        when(authRateLimitService.resolveClientIp(request)).thenReturn("127.0.0.1");
        when(loginService.login("user@example.com", "password123"))
                .thenReturn(
                        new LoginService.LoginResult(
                                1L,
                                "user@example.com",
                                "USER",
                                "access-token",
                                "Bearer",
                                900L,
                                "refresh-token",
                                604800L));

        authController.login(requestDto, request, response);

        verify(authRateLimitService).resetLoginFailures("user@example.com");
        verify(refreshTokenCookieService)
                .setRefreshToken(response, "refresh-token", Duration.ofSeconds(604800L));
    }

    @Test
    void reissueRejectsWhenRefreshCookieMissing() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        when(authRateLimitService.resolveClientIp(request)).thenReturn("127.0.0.1");
        when(refreshTokenCookieService.resolveRefreshToken(request)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authController.reissue(request, response))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.REFRESH_TOKEN_INVALID));
    }

    @Test
    void logoutRejectsWhenRefreshCookieMissing() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        when(refreshTokenCookieService.resolveRefreshToken(request)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authController.logout(request, response, "Bearer access-token"))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.REFRESH_TOKEN_INVALID));
    }
}
