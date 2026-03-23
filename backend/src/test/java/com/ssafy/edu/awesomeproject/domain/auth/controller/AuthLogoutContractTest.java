package com.ssafy.edu.awesomeproject.domain.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.cookie;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.edu.awesomeproject.common.security.jwt.JwtTokenSpec;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.PasswordHashService;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import com.ssafy.edu.awesomeproject.domain.auth.token.StoredRefreshToken;
import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import java.lang.reflect.Constructor;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockCookie;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest(
        properties = {
            "aws.s3.bucket=test-bucket",
            "aws.s3.region=ap-northeast-2",
            "ssafy.api.key=test-ssafy-key",
            "auth.jwt.refresh-cookie.name=__Host-refresh",
            "auth.jwt.refresh-cookie.path=/",
            "auth.jwt.refresh-cookie.secure=true",
            "auth.jwt.refresh-cookie.same-site=Lax"
        })
@AutoConfigureMockMvc
class AuthLogoutContractTest {

    @Autowired private MockMvc mockMvc;

    @Autowired private UserRepository userRepository;

    @Autowired private CohortRepository cohortRepository;

    @Autowired private PasswordHashService passwordHashService;

    @Autowired private AccessTokenService accessTokenService;

    @MockBean private RefreshTokenStore refreshTokenStore;

    private static final String LOGIN_PATH = "/auth/login";
    private static final String LOGOUT_PATH = "/auth/logout";
    private static final String REFRESH_COOKIE_NAME = "__Host-refresh";
    private static final String FIXTURE_PASSWORD = "Password123!";
    private static final String PRIMARY_EMAIL = "logout-contract-primary@example.com";
    private static final String SECONDARY_EMAIL = "logout-contract-secondary@example.com";

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final java.util.Map<String, StoredRefreshToken> storedRefreshTokenBySessionId =
            new ConcurrentHashMap<>();
    private final Set<String> blacklistedRefreshTokenIds = ConcurrentHashMap.newKeySet();
    private final Set<String> blacklistedAccessTokenIds = ConcurrentHashMap.newKeySet();

    @BeforeEach
    void setUp() throws Exception {
        storedRefreshTokenBySessionId.clear();
        blacklistedRefreshTokenIds.clear();
        blacklistedAccessTokenIds.clear();

        userRepository.deleteAll();
        cohortRepository.deleteAll();

        Cohort cohort = newCohort("A605", 605);
        Cohort persistedCohort = cohortRepository.save(cohort);

        userRepository.save(newUser(PRIMARY_EMAIL, "contract-primary", persistedCohort));
        userRepository.save(newUser(SECONDARY_EMAIL, "contract-secondary", persistedCohort));

        org.mockito.BDDMockito.willAnswer(
                        invocation -> {
                            String sessionId = invocation.getArgument(0);
                            String refreshToken = invocation.getArgument(1);
                            String tokenId = invocation.getArgument(2);
                            Long userId = invocation.getArgument(3);
                            storedRefreshTokenBySessionId.put(
                                    sessionId,
                                    new StoredRefreshToken(refreshToken, tokenId, userId));
                            return null;
                        })
                .given(refreshTokenStore)
                .save(anyString(), anyString(), anyString(), any(Long.class), any());

        org.mockito.BDDMockito.given(refreshTokenStore.findBySessionId(anyString()))
                .willAnswer(
                        invocation ->
                                Optional.ofNullable(
                                        storedRefreshTokenBySessionId.get(
                                                invocation.getArgument(0))));

        org.mockito.BDDMockito.given(refreshTokenStore.matches(anyString(), anyString()))
                .willAnswer(
                        invocation -> {
                            String sessionId = invocation.getArgument(0);
                            String refreshToken = invocation.getArgument(1);
                            StoredRefreshToken storedRefreshToken =
                                    storedRefreshTokenBySessionId.get(sessionId);
                            return storedRefreshToken != null
                                    && storedRefreshToken.tokenHash().equals(refreshToken);
                        });

        org.mockito.BDDMockito.willAnswer(
                        invocation -> {
                            storedRefreshTokenBySessionId.remove(invocation.getArgument(0));
                            return null;
                        })
                .given(refreshTokenStore)
                .deleteBySessionId(anyString());

        org.mockito.BDDMockito.willAnswer(
                        invocation -> {
                            storedRefreshTokenBySessionId.remove(invocation.getArgument(0));
                            return null;
                        })
                .given(refreshTokenStore)
                .invalidateSession(anyString());

        org.mockito.BDDMockito.willAnswer(
                        invocation -> {
                            blacklistedRefreshTokenIds.add(invocation.getArgument(0));
                            return null;
                        })
                .given(refreshTokenStore)
                .blacklistRefreshToken(anyString(), any());

        org.mockito.BDDMockito.given(refreshTokenStore.isRefreshTokenBlacklisted(anyString()))
                .willAnswer(
                        invocation ->
                                blacklistedRefreshTokenIds.contains(invocation.getArgument(0)));

        org.mockito.BDDMockito.willAnswer(
                        invocation -> {
                            blacklistedAccessTokenIds.add(invocation.getArgument(0));
                            return null;
                        })
                .given(refreshTokenStore)
                .blacklistAccessToken(anyString(), any());

        org.mockito.BDDMockito.given(refreshTokenStore.isAccessTokenBlacklisted(anyString()))
                .willAnswer(
                        invocation ->
                                blacklistedAccessTokenIds.contains(invocation.getArgument(0)));

        org.mockito.BDDMockito.given(refreshTokenStore.resolveTimeToLive(any(Instant.class)))
                .willAnswer(
                        invocation -> {
                            Duration duration =
                                    Duration.between(Instant.now(), invocation.getArgument(0));
                            return duration.isNegative() ? Duration.ZERO : duration;
                        });
    }

    @Test
    void logout_withValidRefreshCookieAndNoAuthorization_returnsSuccessEnvelopeAndClearsCookie()
            throws Exception {
        LoginTokens tokens = loginAndGetTokens(PRIMARY_EMAIL, FIXTURE_PASSWORD);

        mockMvc.perform(
                        post(LOGOUT_PATH)
                                .cookie(new MockCookie(REFRESH_COOKIE_NAME, tokens.refreshToken())))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.message").value("Request processed successfully."))
                .andExpect(jsonPath("$.data.message").value("Logged out."))
                .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                .andExpect(cookie().value(REFRESH_COOKIE_NAME, ""))
                .andExpect(cookie().maxAge(REFRESH_COOKIE_NAME, 0))
                .andExpect(cookie().httpOnly(REFRESH_COOKIE_NAME, true))
                .andExpect(cookie().secure(REFRESH_COOKIE_NAME, true))
                .andExpect(cookie().path(REFRESH_COOKIE_NAME, "/"))
                .andExpect(cookie().sameSite(REFRESH_COOKIE_NAME, "Lax"));
    }

    @Test
    void logout_prefersRefreshCookieOverBodyToken_whenBothProvided() throws Exception {
        LoginTokens tokens = loginAndGetTokens(PRIMARY_EMAIL, FIXTURE_PASSWORD);

        mockMvc.perform(
                        post(LOGOUT_PATH)
                                .cookie(new MockCookie(REFRESH_COOKIE_NAME, tokens.refreshToken()))
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{" + "\"refreshToken\":\"not-a-valid-token\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.data.message").value("Logged out."));
    }

    @Test
    void logout_fallsBackToBodyToken_whenCookieAbsent() throws Exception {
        LoginTokens tokens = loginAndGetTokens(PRIMARY_EMAIL, FIXTURE_PASSWORD);

        mockMvc.perform(
                        post(LOGOUT_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        "{"
                                                + "\"refreshToken\":\"%s\"}"
                                                        .formatted(tokens.refreshToken())))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.data.message").value("Logged out."));
    }

    @Test
    void logout_withMismatchedAccessTokenOwner_preservesCurrentSuccessContract() throws Exception {
        LoginTokens primaryTokens = loginAndGetTokens(PRIMARY_EMAIL, FIXTURE_PASSWORD);
        LoginTokens secondaryTokens = loginAndGetTokens(SECONDARY_EMAIL, FIXTURE_PASSWORD);
        ParsedToken parsedSecondaryAccessToken =
                accessTokenService.parseAccessToken(secondaryTokens.accessToken());

        mockMvc.perform(
                        post(LOGOUT_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        "{"
                                                + "\"refreshToken\":\"%s\"}"
                                                        .formatted(primaryTokens.refreshToken()))
                                .header("Authorization", "Bearer " + secondaryTokens.accessToken()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.message").value("Request processed successfully."))
                .andExpect(jsonPath("$.data.message").value("Logged out."))
                .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                .andExpect(cookie().value(REFRESH_COOKIE_NAME, ""))
                .andExpect(cookie().maxAge(REFRESH_COOKIE_NAME, 0));

        Assertions.assertFalse(
                blacklistedAccessTokenIds.contains(parsedSecondaryAccessToken.tokenId()));
    }

    @Test
    void logout_withInvalidRefreshToken_returnsUnauthorizedInvalidRefreshEnvelope()
            throws Exception {
        mockMvc.perform(
                        post(LOGOUT_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{" + "\"refreshToken\":\"not-a-jwt\"}"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_4"))
                .andExpect(jsonPath("$.message").value("리프레시 토큰이 유효하지 않습니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                .andExpect(cookie().value(REFRESH_COOKIE_NAME, ""))
                .andExpect(cookie().maxAge(REFRESH_COOKIE_NAME, 0));
    }

    @Test
    void logout_withExpiredRefreshToken_returnsUnauthorizedExpiredEnvelopeAndClearsCookie()
            throws Exception {
        String expiredRefreshToken =
                accessTokenService
                        .issue(
                                JwtTokenSpec.refresh(
                                        "1",
                                        UUID.randomUUID().toString(),
                                        "expired-session",
                                        Map.of(),
                                        -1))
                        .accessToken();

        mockMvc.perform(
                        post(LOGOUT_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        "{"
                                                + "\"refreshToken\":\"%s\"}"
                                                        .formatted(expiredRefreshToken)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_3"))
                .andExpect(jsonPath("$.message").value("리프레시 토큰이 만료되었습니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                .andExpect(cookie().value(REFRESH_COOKIE_NAME, ""))
                .andExpect(cookie().maxAge(REFRESH_COOKIE_NAME, 0));
    }

    @Test
    void logout_withBlacklistedRefreshToken_returnsUnauthorizedBlacklistedEnvelopeAndClearsCookie()
            throws Exception {
        LoginTokens tokens = loginAndGetTokens(PRIMARY_EMAIL, FIXTURE_PASSWORD);
        ParsedToken parsedRefreshToken =
                accessTokenService.parseRefreshToken(tokens.refreshToken());
        blacklistedRefreshTokenIds.add(parsedRefreshToken.tokenId());

        mockMvc.perform(
                        post(LOGOUT_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        "{"
                                                + "\"refreshToken\":\"%s\"}"
                                                        .formatted(tokens.refreshToken())))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_7"))
                .andExpect(jsonPath("$.message").value("차단된 리프레시 토큰입니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                .andExpect(cookie().value(REFRESH_COOKIE_NAME, ""))
                .andExpect(cookie().maxAge(REFRESH_COOKIE_NAME, 0));
    }

    private LoginTokens loginAndGetTokens(String email, String password) throws Exception {
        MvcResult loginResult =
                mockMvc.perform(
                                post(LOGIN_PATH)
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content(
                                                """
                                                {
                                                  "email": "%s",
                                                  "password": "%s"
                                                }
                                                """
                                                        .formatted(email, password)))
                        .andExpect(status().isOk())
                        .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                        .andReturn();

        JsonNode body = objectMapper.readTree(loginResult.getResponse().getContentAsString());
        String accessToken = body.path("data").path("accessToken").asText();
        String refreshToken = loginResult.getResponse().getCookie(REFRESH_COOKIE_NAME).getValue();
        return new LoginTokens(accessToken, refreshToken);
    }

    private User newUser(String email, String nickname, Cohort cohort) {
        return new User(
                email,
                passwordHashService.encode(FIXTURE_PASSWORD),
                "Contract User",
                LocalDate.of(1997, 2, 10),
                nickname,
                null,
                true,
                LocalDateTime.of(2026, 3, 20, 10, 0),
                UserRole.USER,
                cohort);
    }

    private Cohort newCohort(String cohortCode, int generationNo) throws Exception {
        Constructor<Cohort> constructor = Cohort.class.getDeclaredConstructor();
        constructor.setAccessible(true);
        Cohort cohort = constructor.newInstance();

        setField(cohort, "cohortCode", cohortCode);
        setField(cohort, "generationNo", generationNo);
        setField(cohort, "startDate", LocalDate.of(2026, 1, 1));
        setField(cohort, "endDate", LocalDate.of(2026, 12, 31));

        return cohort;
    }

    private void setField(Object target, String fieldName, Object value) throws Exception {
        java.lang.reflect.Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(target, value);
    }

    private record LoginTokens(String accessToken, String refreshToken) {}
}
