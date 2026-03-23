package com.ssafy.edu.awesomeproject.common.security.web;

import com.ssafy.edu.awesomeproject.common.security.error.TokenErrorCode;
import com.ssafy.edu.awesomeproject.common.security.error.TokenException;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Component;

@Component
public class CurrentUserExtractor {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    private final AccessTokenService accessTokenService;
    private final RefreshTokenStore refreshTokenStore;
    private final UserRepository userRepository;

    public CurrentUserExtractor(
            AccessTokenService accessTokenService,
            RefreshTokenStore refreshTokenStore,
            UserRepository userRepository) {
        this.accessTokenService = accessTokenService;
        this.refreshTokenStore = refreshTokenStore;
        this.userRepository = userRepository;
    }

    public Long extractUserId(String authorizationHeader) {
        String token = extractBearerToken(authorizationHeader);
        ParsedToken parsedToken = accessTokenService.parseAccessToken(token);
        validateNotBlacklisted(parsedToken);
        return parseUserId(parsedToken);
    }

    public Long extractUserIdFromRequestHeader(HttpServletRequest request) {
        return extractUserId(request.getHeader(AUTHORIZATION_HEADER));
    }

    public CurrentUserAuth extractAuthFromRequestHeader(HttpServletRequest request) {
        String token = extractBearerToken(request.getHeader(AUTHORIZATION_HEADER));
        ParsedToken parsedToken = accessTokenService.parseAccessToken(token);
        validateNotBlacklisted(parsedToken);
        return new CurrentUserAuth(parseUserId(parsedToken), parseUserRole(parsedToken));
    }

    private Long parseUserId(ParsedToken parsedToken) {
        Long userId;
        try {
            userId = Long.parseLong(parsedToken.subject());
        } catch (NumberFormatException exception) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }

        if (!userRepository.existsActiveById(userId)) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }

        return userId;
    }

    private UserRole parseUserRole(ParsedToken parsedToken) {
        Object roleClaim = parsedToken.claims().get("role");
        if (!(roleClaim instanceof String role)) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }

        try {
            return UserRole.valueOf(role);
        } catch (IllegalArgumentException exception) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }
    }

    private String extractBearerToken(String authorizationHeader) {
        if (authorizationHeader == null || authorizationHeader.isBlank()) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }

        if (authorizationHeader.startsWith(BEARER_PREFIX)) {
            String token = authorizationHeader.substring(BEARER_PREFIX.length()).trim();
            if (token.isBlank()) {
                throw new TokenException(TokenErrorCode.TOKEN_INVALID);
            }
            return token;
        }

        return authorizationHeader;
    }

    private void validateNotBlacklisted(ParsedToken parsedToken) {
        if (refreshTokenStore.isAccessTokenBlacklisted(parsedToken.tokenId())) {
            throw new TokenException(TokenErrorCode.TOKEN_BLACKLISTED);
        }
    }

    public record CurrentUserAuth(Long userId, UserRole role) {}
}
