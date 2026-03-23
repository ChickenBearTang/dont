package com.ssafy.edu.awesomeproject.domain.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.cookie;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ssafy.edu.awesomeproject.common.security.jwt.JwtTokenSpec;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.PasswordHashService;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import com.ssafy.edu.awesomeproject.domain.auth.token.ReissueLockStore;
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
public class AuthReissueContractTest {

    @Autowired private MockMvc mockMvc;

    @Autowired private UserRepository userRepository;

    @Autowired private CohortRepository cohortRepository;

    @Autowired private PasswordHashService passwordHashService;

    @Autowired private AccessTokenService accessTokenService;

    @MockBean private RefreshTokenStore refreshTokenStore;

    @MockBean private ReissueLockStore reissueLockStore;

    private static final String LOGIN_PATH = "/auth/login";
    private static final String REISSUE_PATH = "/auth/reissue";
    private static final String REFRESH_COOKIE_NAME = "__Host-refresh";
    private static final String FIXTURE_EMAIL = "reissue-contract@example.com";
    private static final String FIXTURE_PASSWORD = "Password123!";

    private final Map<String, StoredRefreshToken> storedRefreshTokenBySessionId =
            new ConcurrentHashMap<>();
    private final Set<String> blacklistedRefreshTokenIds = ConcurrentHashMap.newKeySet();

    @BeforeEach
    void setUp() throws Exception {
        storedRefreshTokenBySessionId.clear();
        blacklistedRefreshTokenIds.clear();

        userRepository.deleteAll();
        cohortRepository.deleteAll();

        Cohort cohort = newCohort("A605", 605);
        Cohort persistedCohort = cohortRepository.save(cohort);

        User user =
                new User(
                        FIXTURE_EMAIL,
                        passwordHashService.encode(FIXTURE_PASSWORD),
                        "Contract User",
                        LocalDate.of(1997, 2, 10),
                        "contract-user",
                        null,
                        true,
                        LocalDateTime.of(2026, 3, 20, 10, 0),
                        UserRole.USER,
                        persistedCohort);
        userRepository.save(user);

        org.mockito.BDDMockito.given(reissueLockStore.tryAcquireBySessionId(anyString(), any()))
                .willReturn(true);
        org.mockito.BDDMockito.willDoNothing()
                .given(reissueLockStore)
                .releaseBySessionId(anyString());

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

        org.mockito.BDDMockito.willDoNothing()
                .given(refreshTokenStore)
                .blacklistAccessToken(anyString(), any());
        org.mockito.BDDMockito.given(refreshTokenStore.isAccessTokenBlacklisted(anyString()))
                .willReturn(false);

        org.mockito.BDDMockito.given(refreshTokenStore.resolveTimeToLive(any(Instant.class)))
                .willAnswer(
                        invocation -> {
                            Duration duration =
                                    Duration.between(Instant.now(), invocation.getArgument(0));
                            return duration.isNegative() ? Duration.ZERO : duration;
                        });
    }

    @Test
    void reissue_prefersRefreshCookieOverBodyToken_whenBothProvided() throws Exception {
        String validRefreshToken = loginAndGetRefreshToken();

        MvcResult reissueResult =
                mockMvc.perform(
                                post(REISSUE_PATH)
                                        .cookie(
                                                new MockCookie(
                                                        REFRESH_COOKIE_NAME, validRefreshToken))
                                        .contentType(MediaType.APPLICATION_JSON)
                                        .content("{" + "\"refreshToken\":\"not-a-valid-token\"}"))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$.success").value(true))
                        .andExpect(jsonPath("$.code").value("SUCCESS"))
                        .andExpect(jsonPath("$.message").value("Request processed successfully."))
                        .andExpect(jsonPath("$.data.accessToken").isNotEmpty())
                        .andExpect(jsonPath("$.data.tokenType").value("Bearer"))
                        .andExpect(jsonPath("$.data.expiresInSeconds").value(3600))
                        .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                        .andExpect(cookie().httpOnly(REFRESH_COOKIE_NAME, true))
                        .andExpect(cookie().secure(REFRESH_COOKIE_NAME, true))
                        .andExpect(cookie().path(REFRESH_COOKIE_NAME, "/"))
                        .andExpect(cookie().sameSite(REFRESH_COOKIE_NAME, "Lax"))
                        .andExpect(cookie().maxAge(REFRESH_COOKIE_NAME, 86400))
                        .andReturn();

        String rotatedRefreshToken =
                reissueResult.getResponse().getCookie(REFRESH_COOKIE_NAME).getValue();
        org.junit.jupiter.api.Assertions.assertNotEquals(validRefreshToken, rotatedRefreshToken);
    }

    @Test
    void reissue_withRefreshCookieOnly_returnsSuccessAndRotatesRefreshCookie() throws Exception {
        String validRefreshToken = loginAndGetRefreshToken();

        MvcResult reissueResult =
                mockMvc.perform(
                                post(REISSUE_PATH)
                                        .cookie(
                                                new MockCookie(
                                                        REFRESH_COOKIE_NAME, validRefreshToken)))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$.success").value(true))
                        .andExpect(jsonPath("$.code").value("SUCCESS"))
                        .andExpect(jsonPath("$.message").value("Request processed successfully."))
                        .andExpect(jsonPath("$.data.accessToken").isNotEmpty())
                        .andExpect(jsonPath("$.data.tokenType").value("Bearer"))
                        .andExpect(jsonPath("$.data.expiresInSeconds").value(3600))
                        .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                        .andExpect(cookie().httpOnly(REFRESH_COOKIE_NAME, true))
                        .andExpect(cookie().secure(REFRESH_COOKIE_NAME, true))
                        .andExpect(cookie().path(REFRESH_COOKIE_NAME, "/"))
                        .andExpect(cookie().sameSite(REFRESH_COOKIE_NAME, "Lax"))
                        .andExpect(cookie().maxAge(REFRESH_COOKIE_NAME, 86400))
                        .andReturn();

        String rotatedRefreshToken =
                reissueResult.getResponse().getCookie(REFRESH_COOKIE_NAME).getValue();
        org.junit.jupiter.api.Assertions.assertNotEquals(validRefreshToken, rotatedRefreshToken);
    }

    @Test
    void reissue_fallsBackToBodyToken_whenCookieAbsent() throws Exception {
        String validRefreshToken = loginAndGetRefreshToken();

        mockMvc.perform(
                        post(REISSUE_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        "{"
                                                + "\"refreshToken\":\"%s\"}"
                                                        .formatted(validRefreshToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.message").value("Request processed successfully."))
                .andExpect(jsonPath("$.data.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.data.tokenType").value("Bearer"))
                .andExpect(jsonPath("$.data.expiresInSeconds").value(3600))
                .andExpect(cookie().exists(REFRESH_COOKIE_NAME));
    }

    @Test
    void reissue_withNullBodyAndNoCookie_returnsUnauthorizedInvalidRefreshEnvelope()
            throws Exception {
        mockMvc.perform(post(REISSUE_PATH).contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_4"))
                .andExpect(jsonPath("$.message").value("리프레시 토큰이 유효하지 않습니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().doesNotExist(REFRESH_COOKIE_NAME));
    }

    @Test
    void reissue_withBlankBodyRefreshToken_returnsUnauthorizedInvalidRefreshEnvelope()
            throws Exception {
        mockMvc.perform(
                        post(REISSUE_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{" + "\"refreshToken\":\"   \"}"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_4"))
                .andExpect(jsonPath("$.message").value("리프레시 토큰이 유효하지 않습니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().doesNotExist(REFRESH_COOKIE_NAME));
    }

    @Test
    void reissue_withInvalidBodyRefreshToken_returnsUnauthorizedInvalidRefreshEnvelope()
            throws Exception {
        mockMvc.perform(
                        post(REISSUE_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{" + "\"refreshToken\":\"not-a-jwt\"}"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_4"))
                .andExpect(jsonPath("$.message").value("리프레시 토큰이 유효하지 않습니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().doesNotExist(REFRESH_COOKIE_NAME));
    }

    @Test
    void reissue_withExpiredBodyRefreshToken_returnsUnauthorizedExpiredRefreshEnvelope()
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
                        post(REISSUE_PATH)
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
                .andExpect(cookie().doesNotExist(REFRESH_COOKIE_NAME));
    }

    @Test
    void reissue_withBlacklistedRefreshToken_returnsUnauthorizedBlacklistedRefreshEnvelope()
            throws Exception {
        String validRefreshToken = loginAndGetRefreshToken();
        ParsedToken parsedRefreshToken = accessTokenService.parseRefreshToken(validRefreshToken);
        blacklistedRefreshTokenIds.add(parsedRefreshToken.tokenId());

        mockMvc.perform(
                        post(REISSUE_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        "{"
                                                + "\"refreshToken\":\"%s\"}"
                                                        .formatted(validRefreshToken)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_7"))
                .andExpect(jsonPath("$.message").value("차단된 리프레시 토큰입니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().doesNotExist(REFRESH_COOKIE_NAME));
    }

    @Test
    void reissue_withInvalidCookieAndValidBodyToken_prefersCookieAndDoesNotEmitRefreshCookie()
            throws Exception {
        String validRefreshToken = loginAndGetRefreshToken();

        mockMvc.perform(
                        post(REISSUE_PATH)
                                .cookie(new MockCookie(REFRESH_COOKIE_NAME, "not-a-jwt"))
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        "{"
                                                + "\"refreshToken\":\"%s\"}"
                                                        .formatted(validRefreshToken)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_4"))
                .andExpect(jsonPath("$.message").value("리프레시 토큰이 유효하지 않습니다."))
                .andExpect(jsonPath("$.data").doesNotExist())
                .andExpect(cookie().doesNotExist(REFRESH_COOKIE_NAME));
    }

    private String loginAndGetRefreshToken() throws Exception {
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
                                                        .formatted(
                                                                FIXTURE_EMAIL, FIXTURE_PASSWORD)))
                        .andExpect(status().isOk())
                        .andExpect(cookie().exists(REFRESH_COOKIE_NAME))
                        .andReturn();

        return loginResult.getResponse().getCookie(REFRESH_COOKIE_NAME).getValue();
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
}
