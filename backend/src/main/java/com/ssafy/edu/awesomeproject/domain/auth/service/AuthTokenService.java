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
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class AuthTokenService {
    private static final String BEARER_PREFIX = "Bearer ";

    private final AccessTokenService accessTokenService;
    private final UserRepository userRepository;
    private final RefreshTokenStore refreshTokenStore;
    private final long accessTokenTtlSeconds;
    private final long refreshTokenTtlSeconds;

    public AuthTokenService(
            AccessTokenService accessTokenService,
            UserRepository userRepository,
            RefreshTokenStore refreshTokenStore,
            @Value("${auth.jwt.access-token-ttl-seconds}") long accessTokenTtlSeconds,
            @Value("${auth.jwt.refresh-token-ttl-seconds}") long refreshTokenTtlSeconds) {
        this.accessTokenService = accessTokenService;
        this.userRepository = userRepository;
        this.refreshTokenStore = refreshTokenStore;
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
        validateRefreshToken(parsedRefreshToken, refreshToken);

        Long userId = parseUserId(parsedRefreshToken.subject());

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new AuthException(AuthErrorCode.REFRESH_TOKEN_INVALID));

        IssuedToken issuedAccessToken = issueAccessToken(user);
        IssuedToken issuedRefreshToken = issueRefreshToken(user, parsedRefreshToken.sessionId());
        ParsedToken parsedRotatedRefreshToken = parseRefreshToken(issuedRefreshToken.accessToken());

        refreshTokenStore.blacklistRefreshToken(
                parsedRefreshToken.tokenId(),
                refreshTokenStore.resolveTimeToLive(parsedRefreshToken.expiresAt()));
        refreshTokenStore.save(
                parsedRefreshToken.sessionId(),
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
    }

    @Transactional
    public void logout(String refreshToken, String authorizationHeader) {
        ParsedToken parsedRefreshToken = parseRefreshToken(refreshToken);
        validateRefreshToken(parsedRefreshToken, refreshToken);

        ParsedToken parsedAccessToken = parseAccessToken(extractBearerToken(authorizationHeader));
        validateAccessTokenOwner(parsedRefreshToken, parsedAccessToken);

        refreshTokenStore.deleteBySessionId(parsedRefreshToken.sessionId());
        refreshTokenStore.blacklistAccessToken(
                parsedAccessToken.tokenId(),
                refreshTokenStore.resolveTimeToLive(parsedAccessToken.expiresAt()));
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
            throw new TokenException(TokenErrorCode.TOKEN_BLACKLISTED);
        }

        if (!refreshTokenStore.matches(parsedRefreshToken.sessionId(), refreshToken)) {
            throw new AuthException(AuthErrorCode.REFRESH_TOKEN_INVALID);
        }
    }

    private ParsedToken parseRefreshToken(String refreshToken) {
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
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }
    }

    private AuthException translateRefreshTokenException(TokenException exception) {
        if (exception.getErrorCode() == TokenErrorCode.TOKEN_EXPIRED) {
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
