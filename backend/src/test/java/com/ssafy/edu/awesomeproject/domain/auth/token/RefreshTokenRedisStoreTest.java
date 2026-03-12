package com.ssafy.edu.awesomeproject.domain.auth.token;

import static org.assertj.core.api.Assertions.assertThat;

import com.ssafy.edu.awesomeproject.common.config.CommonBeanConfig;
import java.time.Duration;
import java.time.Instant;
import java.util.function.BooleanSupplier;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.autoconfigure.data.redis.DataRedisTest;
import org.springframework.context.annotation.Import;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataRedisTest
@Testcontainers
@ContextConfiguration(classes = RefreshTokenRedisStoreTest.TestApplication.class)
@Import({
    CommonBeanConfig.class,
    RefreshTokenRedisStore.class,
    RefreshTokenHashService.class,
    TokenTimeToLiveResolver.class,
})
class RefreshTokenRedisStoreTest {
    @SpringBootConfiguration
    @EnableAutoConfiguration
    static class TestApplication {}

    @Container
    static final GenericContainer<?> REDIS_CONTAINER =
            new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);

    @DynamicPropertySource
    static void registerRedisProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.redis.host", REDIS_CONTAINER::getHost);
        registry.add("spring.data.redis.port", REDIS_CONTAINER::getFirstMappedPort);
    }

    @Autowired private RefreshTokenRedisStore refreshTokenRedisStore;

    @Autowired private RefreshTokenHashService refreshTokenHashService;

    @Autowired private StringRedisTemplate stringRedisTemplate;

    @Test
    void saveFindMatchAndDeleteStoreRefreshTokenWithTtl() throws InterruptedException {
        String sessionId = "session-1";
        String refreshToken = "refresh-token-value";
        String refreshTokenId = "refresh-jti-1";
        Long userId = 42L;
        Duration timeToLive = Duration.ofSeconds(2);

        refreshTokenRedisStore.save(sessionId, refreshToken, refreshTokenId, userId, timeToLive);

        StoredRefreshToken storedRefreshToken =
                refreshTokenRedisStore.findBySessionId(sessionId).orElseThrow();
        assertThat(storedRefreshToken.tokenHash())
                .isEqualTo(refreshTokenHashService.hash(refreshToken));
        assertThat(storedRefreshToken.tokenHash()).isNotEqualTo(refreshToken);
        assertThat(storedRefreshToken.tokenId()).isEqualTo(refreshTokenId);
        assertThat(storedRefreshToken.userId()).isEqualTo(userId);
        assertThat(refreshTokenRedisStore.matches(sessionId, refreshToken)).isTrue();
        assertThat(refreshTokenRedisStore.matches(sessionId, refreshToken + "-other")).isFalse();
        assertThat(refreshTokenRedisStore.getTimeToLiveSeconds("rt:" + sessionId))
                .isBetween(0L, 2L);

        waitUntil(() -> refreshTokenRedisStore.findBySessionId(sessionId).isEmpty());

        assertThat(refreshTokenRedisStore.findBySessionId(sessionId)).isEmpty();

        refreshTokenRedisStore.save(
                sessionId, refreshToken, refreshTokenId, userId, Duration.ofSeconds(5));
        refreshTokenRedisStore.deleteBySessionId(sessionId);

        assertThat(refreshTokenRedisStore.findBySessionId(sessionId)).isEmpty();
        assertThat(stringRedisTemplate.hasKey("rt:" + sessionId)).isFalse();
    }

    @Test
    void blacklistRefreshAndAccessTokensWithRemainingTimeToLive() throws InterruptedException {
        String refreshTokenId = "refresh-jti-2";
        String accessTokenId = "access-jti-1";

        refreshTokenRedisStore.blacklistRefreshToken(refreshTokenId, Duration.ofSeconds(2));
        refreshTokenRedisStore.blacklistAccessToken(accessTokenId, Duration.ofSeconds(2));

        assertThat(refreshTokenRedisStore.isRefreshTokenBlacklisted(refreshTokenId)).isTrue();
        assertThat(refreshTokenRedisStore.isAccessTokenBlacklisted(accessTokenId)).isTrue();
        assertThat(refreshTokenRedisStore.getTimeToLiveSeconds("bl:rt:" + refreshTokenId))
                .isBetween(0L, 2L);
        assertThat(refreshTokenRedisStore.getTimeToLiveSeconds("bl:at:" + accessTokenId))
                .isBetween(0L, 2L);

        waitUntil(() -> !refreshTokenRedisStore.isRefreshTokenBlacklisted(refreshTokenId));
        waitUntil(() -> !refreshTokenRedisStore.isAccessTokenBlacklisted(accessTokenId));

        assertThat(refreshTokenRedisStore.isRefreshTokenBlacklisted(refreshTokenId)).isFalse();
        assertThat(refreshTokenRedisStore.isAccessTokenBlacklisted(accessTokenId)).isFalse();
    }

    @Test
    void resolveTimeToLiveUsesExpirationInstant() {
        Duration timeToLive =
                refreshTokenRedisStore.resolveTimeToLive(Instant.now().plusSeconds(5));

        assertThat(timeToLive).isBetween(Duration.ofSeconds(4), Duration.ofSeconds(5));
    }

    @Test
    void invalidateSessionDeletesRefreshKey() {
        String sessionId = "session-2";

        refreshTokenRedisStore.save(sessionId, "refresh", "jti", 100L, Duration.ofSeconds(10));
        assertThat(refreshTokenRedisStore.findBySessionId(sessionId)).isPresent();

        refreshTokenRedisStore.invalidateSession(sessionId);

        assertThat(refreshTokenRedisStore.findBySessionId(sessionId)).isEmpty();
    }

    private void waitUntil(BooleanSupplier condition) throws InterruptedException {
        long deadline = System.currentTimeMillis() + 5000L;
        while (System.currentTimeMillis() < deadline) {
            if (condition.getAsBoolean()) {
                return;
            }

            Thread.sleep(100L);
        }

        throw new AssertionError("Condition was not satisfied within 5 seconds.");
    }
}
