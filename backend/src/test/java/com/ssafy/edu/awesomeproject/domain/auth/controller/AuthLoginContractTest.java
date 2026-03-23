package com.ssafy.edu.awesomeproject.domain.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.cookie;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.PasswordHashService;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import java.lang.reflect.Constructor;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

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
public class AuthLoginContractTest {

    @Autowired private MockMvc mockMvc;

    @Autowired private UserRepository userRepository;

    @Autowired private CohortRepository cohortRepository;

    @Autowired private PasswordHashService passwordHashService;

    @MockBean private RefreshTokenStore refreshTokenStore;

    private static final String LOGIN_PATH = "/auth/login";
    private static final String FIXTURE_EMAIL = "login-contract@example.com";
    private static final String FIXTURE_PASSWORD = "Password123!";
    private static final String REFRESH_COOKIE_NAME = "__Host-refresh";

    private User persistedUser;

    @BeforeEach
    void setUp() throws Exception {
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
        persistedUser = userRepository.save(user);

        org.mockito.BDDMockito.given(refreshTokenStore.resolveTimeToLive(any()))
                .willReturn(Duration.ofSeconds(86400));
    }

    @Test
    void login_withValidCredentials_returnsSuccessEnvelopeAndSetsRefreshCookie() throws Exception {
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
                                                .formatted(FIXTURE_EMAIL, FIXTURE_PASSWORD)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value("SUCCESS"))
                .andExpect(jsonPath("$.data.userId").value(extractId(persistedUser)))
                .andExpect(jsonPath("$.data.email").value(FIXTURE_EMAIL))
                .andExpect(jsonPath("$.data.userRole").value(UserRole.USER.name()))
                .andExpect(jsonPath("$.data.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.data.tokenType").value("Bearer"))
                .andExpect(jsonPath("$.data.expiresInSeconds").value(3600))
                .andExpect(cookie().exists(REFRESH_COOKIE_NAME));
    }

    @Test
    void login_withMalformedPayload_returnsValidationFailureEnvelope() throws Exception {
        mockMvc.perform(
                        post(LOGIN_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"email\":\"invalid-email\",\"password\":\"123\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("COMMON_400_2"));
    }

    @Test
    void login_withWrongPassword_returnsUnauthorizedBadCredentialsEnvelope() throws Exception {
        mockMvc.perform(
                        post(LOGIN_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {
                                          "email": "%s",
                                          "password": "wrongPassword123!"
                                        }
                                        """
                                                .formatted(FIXTURE_EMAIL)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_2"));
    }

    @Test
    void login_withNonexistentUser_returnsUnauthorizedBadCredentialsEnvelope() throws Exception {
        mockMvc.perform(
                        post(LOGIN_PATH)
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {
                                          "email": "missing-user@example.com",
                                          "password": "%s"
                                        }
                                        """
                                                .formatted(FIXTURE_PASSWORD)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.code").value("AUTH_401_2"));
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

    private Long extractId(User user) throws Exception {
        java.lang.reflect.Field idField = User.class.getDeclaredField("id");
        idField.setAccessible(true);
        return (Long) idField.get(user);
    }
}
