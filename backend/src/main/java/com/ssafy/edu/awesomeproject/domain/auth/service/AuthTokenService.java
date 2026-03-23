package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.common.security.error.TokenErrorCode;
import com.ssafy.edu.awesomeproject.common.security.error.TokenException;
import com.ssafy.edu.awesomeproject.common.security.jwt.IssuedToken;
import com.ssafy.edu.awesomeproject.common.security.jwt.JwtTokenSpec;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import com.ssafy.edu.awesomeproject.domain.auth.token.ReissueLockStore;
import com.ssafy.edu.awesomeproject.domain.auth.token.StoredRefreshToken;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class AuthTokenService {
    private static final String BEARER_PREFIX = "Bearer ";
    private static final Duration REISSUE_LOCK_TTL = Duration.ofSeconds(10);
    private static final Logger log = LoggerFactory.getLogger(AuthTokenService.class);

    private final AccessTokenService accessTokenService;
    private final UserRepository userRepository;
    private final RefreshTokenStore refreshTokenStore;
    private final ReissueLockStore reissueLockStore;
    private final long accessTokenTtlSeconds;
    private final long refreshTokenTtlSeconds;

    public AuthTokenService(
            AccessTokenService accessTokenService,
            UserRepository userRepository,
            RefreshTokenStore refreshTokenStore,
            ReissueLockStore reissueLockStore,
            @Value("${auth.jwt.access-token-ttl-seconds}") long accessTokenTtlSeconds,
            @Value("${auth.jwt.refresh-token-ttl-seconds}") long refreshTokenTtlSeconds) {
        this.accessTokenService = accessTokenService;
        this.userRepository = userRepository;
        this.refreshTokenStore = refreshTokenStore;
        this.reissueLockStore = reissueLockStore;
        this.accessTokenTtlSeconds = accessTokenTtlSeconds;
        this.refreshTokenTtlSeconds = refreshTokenTtlSeconds;
    }

    @Transactional
    public LoginTokenResult issueLoginTokens(User user) {
        String sessionId = UUID.randomUUID().toString();
        IssuedToken issuedAccessToken = issueAccessToken(user);
        IssuedToken issuedRefreshToken = issueRefreshToken(user, sessionId);
        ParsedToken parsedRefreshToken = parseRefreshToken(issuedRefreshToken.accessToken());

        refreshTokenStore.save(
                sessionId,
                issuedRefreshToken.accessToken(),
                parsedRefreshToken.tokenId(),
                user.getId(),
                refreshTokenStore.resolveTimeToLive(parsedRefreshToken.expiresAt()));

        return new LoginTokenResult(
                issuedAccessToken.accessToken(),
                issuedAccessToken.tokenType(),
                issuedAccessToken.expiresInSeconds(),
                issuedRefreshToken.accessToken(),
                refreshTokenTtlSeconds);
    }

    public ReissueTokenResult reissue(String refreshToken) {
        ParsedToken parsedRefreshToken = parseRefreshToken(refreshToken);
        String sessionId = parsedRefreshToken.sessionId();

        if (!reissueLockStore.tryAcquireBySessionId(sessionId, REISSUE_LOCK_TTL)) {
            log.warn("auth.reissue.lock_conflict sid={}", sessionId);
            throw new AuthException(AuthErrorCode.AUTHENTICATION_FAILED);
        }

        try {
            validateRefreshToken(parsedRefreshToken, refreshToken);

            Long userId = parseUserId(parsedRefreshToken.subject());

            User user =
                    userRepository
                            .findActiveById(userId)
                            .orElseThrow(
                                    () -> new AuthException(AuthErrorCode.REFRESH_TOKEN_INVALID));

            IssuedToken issuedAccessToken = issueAccessToken(user);
            IssuedToken issuedRefreshToken = issueRefreshToken(user, sessionId);
            ParsedToken parsedRotatedRefreshToken =
                    parseRefreshToken(issuedRefreshToken.accessToken());

            refreshTokenStore.blacklistRefreshToken(
                    parsedRefreshToken.tokenId(),
                    refreshTokenStore.resolveTimeToLive(parsedRefreshToken.expiresAt()));
            refreshTokenStore.save(
                    sessionId,
                    issuedRefreshToken.accessToken(),
                    parsedRotatedRefreshToken.tokenId(),
                    userId,
                    refreshTokenStore.resolveTimeToLive(parsedRotatedRefreshToken.expiresAt()));

            return new ReissueTokenResult(
                    issuedAccessToken.accessToken(),
                    issuedAccessToken.tokenType(),
                    issuedAccessToken.expiresInSeconds(),
                    issuedRefreshToken.accessToken(),
                    issuedRefreshToken.expiresInSeconds());
        } finally {
            reissueLockStore.releaseBySessionId(sessionId);
        }
    }

    @Transactional
    public void logout(String refreshToken, String authorizationHeader) {
        ParsedToken parsedRefreshToken = parseRefreshToken(refreshToken);
        validateRefreshToken(parsedRefreshToken, refreshToken);

        refreshTokenStore.deleteBySessionId(parsedRefreshToken.sessionId());
        blacklistAccessTokenIfPossible(parsedRefreshToken, authorizationHeader);
    }

    @Transactional
    public void blacklistAccessTokenByAuthorizationHeader(
            String authorizationHeader, Long expectedUserId) {
        if (authorizationHeader == null || authorizationHeader.isBlank()) {
            return;
        }

        try {
            ParsedToken parsedAccessToken =
                    parseAccessToken(extractBearerToken(authorizationHeader));
            if (!String.valueOf(expectedUserId).equals(parsedAccessToken.subject())) {
                throw new AuthException(AuthErrorCode.AUTHENTICATION_FAILED);
            }

            refreshTokenStore.blacklistAccessToken(
                    parsedAccessToken.tokenId(),
                    refreshTokenStore.resolveTimeToLive(parsedAccessToken.expiresAt()));
        } catch (TokenException | AuthException exception) {
            log.warn(
                    "auth.access_blacklist_skipped userId={} reason={}",
                    expectedUserId,
                    exception.getErrorCode().code());
        }
    }

    private IssuedToken issueAccessToken(User user) {
        JwtTokenSpec jwtTokenSpec =
                JwtTokenSpec.access(
                        String.valueOf(user.getId()),
                        UUID.randomUUID().toString(),
                        Map.of(
                                "email", user.getEmail(),
                                "role", user.getUserRole()),
                        accessTokenTtlSeconds);

        return accessTokenService.issue(jwtTokenSpec);
    }

    private IssuedToken issueRefreshToken(User user, String sessionId) {
        JwtTokenSpec jwtTokenSpec =
                JwtTokenSpec.refresh(
                        String.valueOf(user.getId()),
                        UUID.randomUUID().toString(),
                        sessionId,
                        Map.of(),
                        refreshTokenTtlSeconds);

        return accessTokenService.issue(jwtTokenSpec);
    }

    private Long parseUserId(String subject) {
        try {
            return Long.valueOf(subject);
        } catch (NumberFormatException exception) {
            throw new AuthException(AuthErrorCode.REFRESH_TOKEN_INVALID);
        }
    }

    private void validateRefreshToken(ParsedToken parsedRefreshToken, String refreshToken) {
        if (refreshTokenStore.isRefreshTokenBlacklisted(parsedRefreshToken.tokenId())) {
            throw new AuthException(AuthErrorCode.REFRESH_TOKEN_BLACKLISTED);
        }

        StoredRefreshToken storedRefreshToken =
                refreshTokenStore
                        .findBySessionId(parsedRefreshToken.sessionId())
                        .orElseThrow(() -> new AuthException(AuthErrorCode.REFRESH_TOKEN_INVALID));

        if (!refreshTokenStore.matches(parsedRefreshToken.sessionId(), refreshToken)) {
            refreshTokenStore.invalidateSession(parsedRefreshToken.sessionId());
            refreshTokenStore.blacklistRefreshToken(
                    parsedRefreshToken.tokenId(),
                    refreshTokenStore.resolveTimeToLive(parsedRefreshToken.expiresAt()));
            log.warn(
                    "auth.reissue.reuse_detected sid={} userId={} presentedJti={} storedJti={}",
                    parsedRefreshToken.sessionId(),
                    storedRefreshToken.userId(),
                    parsedRefreshToken.tokenId(),
                    storedRefreshToken.tokenId());
            throw new AuthException(AuthErrorCode.REFRESH_REUSE_DETECTED);
        }
    }

    private ParsedToken parseRefreshToken(String refreshToken) {
        if (refreshToken == null || refreshToken.isBlank()) {
            throw new AuthException(AuthErrorCode.REFRESH_TOKEN_INVALID);
        }

        try {
            return accessTokenService.parseRefreshToken(refreshToken);
        } catch (TokenException exception) {
            throw translateRefreshTokenException(exception);
        }
    }

    private ParsedToken parseAccessToken(String accessToken) {
        return accessTokenService.parseAccessToken(accessToken);
    }

    private void validateAccessTokenOwner(
            ParsedToken parsedRefreshToken, ParsedToken parsedAccessToken) {
        if (!parsedRefreshToken.subject().equals(parsedAccessToken.subject())) {
            throw new AuthException(AuthErrorCode.AUTHENTICATION_FAILED);
        }
    }

    private void blacklistAccessTokenIfPossible(
            ParsedToken parsedRefreshToken, String authorizationHeader) {
        if (authorizationHeader == null || authorizationHeader.isBlank()) {
            return;
        }

        try {
            ParsedToken parsedAccessToken =
                    parseAccessToken(extractBearerToken(authorizationHeader));
            validateAccessTokenOwner(parsedRefreshToken, parsedAccessToken);

            refreshTokenStore.blacklistAccessToken(
                    parsedAccessToken.tokenId(),
                    refreshTokenStore.resolveTimeToLive(parsedAccessToken.expiresAt()));
        } catch (TokenException | AuthException exception) {
            log.warn(
                    "auth.logout.access_blacklist_skipped sid={} reason={}",
                    parsedRefreshToken.sessionId(),
                    exception.getErrorCode().code());
        }
    }

    private AuthException translateRefreshTokenException(TokenException exception) {
        if (exception.getErrorCode() == TokenErrorCode.REFRESH_TOKEN_EXPIRED) {
            return new AuthException(AuthErrorCode.REFRESH_TOKEN_EXPIRED, exception.getDetails());
        }

        return new AuthException(AuthErrorCode.REFRESH_TOKEN_INVALID, exception.getDetails());
    }

    private String extractBearerToken(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith(BEARER_PREFIX)) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }

        String accessToken = authorizationHeader.substring(BEARER_PREFIX.length()).trim();
        if (accessToken.isBlank()) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }

        return accessToken;
    }

    public record LoginTokenResult(
            String accessToken,
            String tokenType,
            long expiresInSeconds,
            String refreshToken,
            long refreshTokenExpiresInSeconds) {}

    public record ReissueTokenResult(
            String accessToken,
            String tokenType,
            long expiresInSeconds,
            String refreshToken,
            long refreshTokenExpiresInSeconds) {}
}
