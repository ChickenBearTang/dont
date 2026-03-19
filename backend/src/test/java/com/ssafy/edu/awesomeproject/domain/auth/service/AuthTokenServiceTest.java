package com.ssafy.edu.awesomeproject.domain.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.common.security.jwt.IssuedToken;
import com.ssafy.edu.awesomeproject.common.security.jwt.JwtTokenSpec;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import com.ssafy.edu.awesomeproject.domain.auth.token.ReissueLockStore;
import com.ssafy.edu.awesomeproject.domain.auth.token.StoredRefreshToken;
import java.time.Duration;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class AuthTokenServiceTest {
    private static final String JWT_SECRET =
            "0123456789012345678901234567890123456789012345678901234567890123";

    @Mock private UserRepository userRepository;

    @Mock private RefreshTokenStore refreshTokenStore;

    @Mock private ReissueLockStore reissueLockStore;

    private AccessTokenService accessTokenService;
    private AuthTokenService authTokenService;

    @BeforeEach
    void setUp() {
        accessTokenService = new AccessTokenService(JWT_SECRET, "awesome-project");
        authTokenService =
                new AuthTokenService(
                        accessTokenService,
                        userRepository,
                        refreshTokenStore,
                        reissueLockStore,
                        900L,
                        604800L);
    }

    @Test
    void issueLoginTokensStoresRefreshTokenBySessionId() {
        User user = createUser(1L);
        Duration refreshTimeToLive = Duration.ofDays(7);
        when(refreshTokenStore.resolveTimeToLive(any())).thenReturn(refreshTimeToLive);

        AuthTokenService.LoginTokenResult result = authTokenService.issueLoginTokens(user);
        ParsedToken parsedRefreshToken =
                accessTokenService.parseRefreshToken(result.refreshToken());

        verify(refreshTokenStore)
                .save(
                        parsedRefreshToken.sessionId(),
                        result.refreshToken(),
                        parsedRefreshToken.tokenId(),
                        user.getId(),
                        refreshTimeToLive);
    }

    @Test
    void reissueRotatesRefreshTokenAndBlacklistsPreviousRefreshToken() {
        User user = createUser(1L);
        String sessionId = "session-id";
        String previousRefreshTokenId = "refresh-jti-1";
        IssuedToken previousRefreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                previousRefreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));
        Duration previousRefreshTokenTtl = Duration.ofDays(6);
        Duration rotatedRefreshTokenTtl = Duration.ofDays(7);

        when(refreshTokenStore.isRefreshTokenBlacklisted(previousRefreshTokenId)).thenReturn(false);
        when(refreshTokenStore.findBySessionId(sessionId))
                .thenReturn(Optional.of(storedToken(previousRefreshTokenId, user.getId())));
        when(refreshTokenStore.matches(sessionId, previousRefreshToken.accessToken()))
                .thenReturn(true);
        when(reissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(10)))
                .thenReturn(true);
        when(refreshTokenStore.resolveTimeToLive(any()))
                .thenReturn(previousRefreshTokenTtl, rotatedRefreshTokenTtl);
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));

        AuthTokenService.ReissueTokenResult result =
                authTokenService.reissue(previousRefreshToken.accessToken());
        ParsedToken parsedRotatedRefreshToken =
                accessTokenService.parseRefreshToken(result.refreshToken());

        verify(refreshTokenStore)
                .blacklistRefreshToken(previousRefreshTokenId, previousRefreshTokenTtl);
        verify(reissueLockStore).releaseBySessionId(sessionId);
        verify(refreshTokenStore)
                .save(
                        sessionId,
                        result.refreshToken(),
                        parsedRotatedRefreshToken.tokenId(),
                        user.getId(),
                        rotatedRefreshTokenTtl);
        assertThat(result.refreshToken()).isNotBlank();
        assertThat(parsedRotatedRefreshToken.sessionId()).isEqualTo(sessionId);
    }

    @Test
    void logoutDeletesRefreshSessionAndBlacklistsCurrentAccessToken() {
        User user = createUser(1L);
        String sessionId = "session-id";
        String refreshTokenId = "refresh-jti-1";
        String accessTokenId = "access-jti-1";
        IssuedToken refreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));
        IssuedToken accessToken =
                accessTokenService.issue(
                        JwtTokenSpec.access(
                                String.valueOf(user.getId()),
                                accessTokenId,
                                Map.of("email", user.getEmail(), "role", user.getUserRole()),
                                900L));
        Duration accessTokenTtl = Duration.ofMinutes(10);

        when(refreshTokenStore.isRefreshTokenBlacklisted(refreshTokenId)).thenReturn(false);
        when(refreshTokenStore.findBySessionId(sessionId))
                .thenReturn(Optional.of(storedToken(refreshTokenId, user.getId())));
        when(refreshTokenStore.matches(sessionId, refreshToken.accessToken())).thenReturn(true);
        when(refreshTokenStore.resolveTimeToLive(any())).thenReturn(accessTokenTtl);

        authTokenService.logout(refreshToken.accessToken(), "Bearer " + accessToken.accessToken());

        verify(refreshTokenStore).deleteBySessionId(sessionId);
        verify(refreshTokenStore).blacklistAccessToken(accessTokenId, accessTokenTtl);
    }

    @Test
    void reissueRejectsBlacklistedRefreshToken() {
        User user = createUser(1L);
        String sessionId = "session-id";
        String refreshTokenId = "refresh-jti-1";
        IssuedToken refreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));

        when(refreshTokenStore.isRefreshTokenBlacklisted(refreshTokenId)).thenReturn(true);
        when(reissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(10)))
                .thenReturn(true);

        assertThatThrownBy(() -> authTokenService.reissue(refreshToken.accessToken()))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.REFRESH_TOKEN_BLACKLISTED));

        verify(refreshTokenStore, never()).matches(any(), any());
        verify(reissueLockStore).releaseBySessionId(sessionId);
    }

    @Test
    void logoutWithDifferentUserAccessStillInvalidatesRefreshSession() {
        User user = createUser(1L);
        User anotherUser = createUser(2L);
        String sessionId = "session-id";
        String refreshTokenId = "refresh-jti-1";
        IssuedToken refreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));
        IssuedToken anotherUserAccessToken =
                accessTokenService.issue(
                        JwtTokenSpec.access(
                                String.valueOf(anotherUser.getId()),
                                "access-jti-2",
                                Map.of(
                                        "email",
                                        anotherUser.getEmail(),
                                        "role",
                                        anotherUser.getUserRole()),
                                900L));

        when(refreshTokenStore.isRefreshTokenBlacklisted(refreshTokenId)).thenReturn(false);
        when(refreshTokenStore.findBySessionId(sessionId))
                .thenReturn(Optional.of(storedToken(refreshTokenId, user.getId())));
        when(refreshTokenStore.matches(sessionId, refreshToken.accessToken())).thenReturn(true);

        authTokenService.logout(
                refreshToken.accessToken(), "Bearer " + anotherUserAccessToken.accessToken());

        verify(refreshTokenStore).deleteBySessionId(sessionId);
        verify(refreshTokenStore, never()).blacklistAccessToken(any(), any());
    }

    @Test
    void logoutWithoutAccessHeaderStillInvalidatesRefreshSession() {
        User user = createUser(1L);
        String sessionId = "session-id";
        String refreshTokenId = "refresh-jti-1";
        IssuedToken refreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));

        when(refreshTokenStore.isRefreshTokenBlacklisted(refreshTokenId)).thenReturn(false);
        when(refreshTokenStore.findBySessionId(sessionId))
                .thenReturn(Optional.of(storedToken(refreshTokenId, user.getId())));
        when(refreshTokenStore.matches(sessionId, refreshToken.accessToken())).thenReturn(true);

        authTokenService.logout(refreshToken.accessToken(), null);

        verify(refreshTokenStore).deleteBySessionId(sessionId);
        verify(refreshTokenStore, never()).blacklistAccessToken(any(), any());
    }

    @Test
    void reissueRejectsWhenLockAcquisitionFails() {
        User user = createUser(1L);
        String sessionId = "session-id";
        String refreshTokenId = "refresh-jti-1";
        IssuedToken refreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));

        when(reissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(10)))
                .thenReturn(false);

        assertThatThrownBy(() -> authTokenService.reissue(refreshToken.accessToken()))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.AUTHENTICATION_FAILED));

        verify(reissueLockStore, never()).releaseBySessionId(any());
    }

    @Test
    void reissueRejectsExpiredRefreshToken() {
        User user = createUser(1L);
        String refreshTokenId = "refresh-jti-expired";
        IssuedToken expiredRefreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                "session-expired",
                                Map.of(),
                                -1L));

        assertThatThrownBy(() -> authTokenService.reissue(expiredRefreshToken.accessToken()))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.REFRESH_TOKEN_EXPIRED));

        verify(reissueLockStore, never()).tryAcquireBySessionId(any(), any());
    }

    @Test
    void reissueRejectsInvalidRefreshToken() {
        assertThatThrownBy(() -> authTokenService.reissue("not-a-jwt-token"))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.REFRESH_TOKEN_INVALID));

        verify(reissueLockStore, never()).tryAcquireBySessionId(any(), any());
    }

    @Test
    void concurrentReissueRequestsFollowSidLockPolicy() {
        User user = createUser(1L);
        String sessionId = "session-lock-policy";
        String refreshTokenId = "refresh-jti-lock";
        IssuedToken refreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));

        when(reissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(10)))
                .thenReturn(false);

        assertThatThrownBy(() -> authTokenService.reissue(refreshToken.accessToken()))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.AUTHENTICATION_FAILED));

        verify(reissueLockStore, never()).releaseBySessionId(any());
        verify(refreshTokenStore, never()).blacklistRefreshToken(any(), any());
    }

    @Test
    void reissueDetectsRefreshReuseAndInvalidatesSession() {
        User user = createUser(1L);
        String sessionId = "session-id";
        String refreshTokenId = "refresh-jti-1";
        IssuedToken refreshToken =
                accessTokenService.issue(
                        JwtTokenSpec.refresh(
                                String.valueOf(user.getId()),
                                refreshTokenId,
                                sessionId,
                                Map.of(),
                                604800L));
        Duration refreshTokenTtl = Duration.ofDays(6);

        when(reissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(10)))
                .thenReturn(true);
        when(refreshTokenStore.isRefreshTokenBlacklisted(refreshTokenId)).thenReturn(false);
        when(refreshTokenStore.findBySessionId(sessionId))
                .thenReturn(Optional.of(storedToken("stored-jti", user.getId())));
        when(refreshTokenStore.matches(sessionId, refreshToken.accessToken())).thenReturn(false);
        when(refreshTokenStore.resolveTimeToLive(any())).thenReturn(refreshTokenTtl);

        assertThatThrownBy(() -> authTokenService.reissue(refreshToken.accessToken()))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.REFRESH_REUSE_DETECTED));

        verify(refreshTokenStore).invalidateSession(sessionId);
        verify(refreshTokenStore).blacklistRefreshToken(refreshTokenId, refreshTokenTtl);
        verify(reissueLockStore).releaseBySessionId(sessionId);
    }

    private User createUser(Long id) {
        User user =
                new User(
                        "test@example.com",
                        "encoded-password",
                        "Tester",
                        java.time.LocalDate.of(1996, 1, 1),
                        "tester",
                        null,
                        true,
                        java.time.LocalDateTime.now(),
                        UserRole.USER,
                        null);
        ReflectionTestUtils.setField(user, "id", id);
        return user;
    }

    private StoredRefreshToken storedToken(String tokenId, Long userId) {
        return new StoredRefreshToken("stored-hash", tokenId, userId);
    }
}
