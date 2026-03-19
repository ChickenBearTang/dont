package com.ssafy.edu.awesomeproject.common.security.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.common.security.error.TokenErrorCode;
import com.ssafy.edu.awesomeproject.common.security.error.TokenException;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.jwt.TokenType;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockHttpServletRequest;

@ExtendWith(MockitoExtension.class)
class CurrentUserExtractorTest {

    @Mock private AccessTokenService accessTokenService;

    @Mock private RefreshTokenStore refreshTokenStore;

    private CurrentUserExtractor currentUserExtractor;

    @BeforeEach
    void setUp() {
        currentUserExtractor = new CurrentUserExtractor(accessTokenService, refreshTokenStore);
    }

    @Test
    void extractAuthRejectsBlacklistedAccessToken() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer access-token");

        ParsedToken parsedToken =
                new ParsedToken(
                        "1",
                        "token-jti",
                        TokenType.ACCESS,
                        null,
                        Instant.now().plusSeconds(60),
                        Map.of("role", "USER"));

        when(accessTokenService.parseAccessToken("access-token")).thenReturn(parsedToken);
        when(refreshTokenStore.isAccessTokenBlacklisted("token-jti")).thenReturn(true);

        assertThatThrownBy(() -> currentUserExtractor.extractAuthFromRequestHeader(request))
                .isInstanceOfSatisfying(
                        TokenException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(TokenErrorCode.TOKEN_BLACKLISTED));
    }

    @Test
    void extractAuthReturnsUserIdAndRoleWhenTokenIsValid() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer access-token");

        ParsedToken parsedToken =
                new ParsedToken(
                        "42",
                        "token-jti",
                        TokenType.ACCESS,
                        null,
                        Instant.now().plusSeconds(60),
                        Map.of("role", "ADMIN"));

        when(accessTokenService.parseAccessToken("access-token")).thenReturn(parsedToken);
        when(refreshTokenStore.isAccessTokenBlacklisted("token-jti")).thenReturn(false);

        CurrentUserExtractor.CurrentUserAuth result =
                currentUserExtractor.extractAuthFromRequestHeader(request);

        assertThat(result.userId()).isEqualTo(42L);
        assertThat(result.role()).isEqualTo(UserRole.ADMIN);
    }

    @Test
    void extractAuthReturnsTokenInvalidWhenBlacklistLookupFails() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer access-token");

        ParsedToken parsedToken =
                new ParsedToken(
                        "42",
                        "token-jti",
                        TokenType.ACCESS,
                        null,
                        Instant.now().plusSeconds(60),
                        Map.of("role", "ADMIN"));

        when(accessTokenService.parseAccessToken("access-token")).thenReturn(parsedToken);
        when(refreshTokenStore.isAccessTokenBlacklisted("token-jti"))
                .thenThrow(new RuntimeException("redis unavailable"));

        assertThatThrownBy(() -> currentUserExtractor.extractAuthFromRequestHeader(request))
                .isInstanceOfSatisfying(
                        TokenException.class,
                        exception ->
                                assertThat(exception.getErrorCode())
                                        .isEqualTo(TokenErrorCode.TOKEN_INVALID));
    }
}
