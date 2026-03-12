package com.ssafy.edu.awesomeproject.domain.auth.token;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Duration;
import java.util.function.BooleanSupplier;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.autoconfigure.data.redis.DataRedisTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataRedisTest
@Testcontainers
@ContextConfiguration(classes = RedisReissueLockStoreTest.TestApplication.class)
@Import(RedisReissueLockStore.class)
class RedisReissueLockStoreTest {
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

    @Autowired private RedisReissueLockStore redisReissueLockStore;

    @Test
    void acquireLockBySessionIdUntilTtlExpires() throws InterruptedException {
        String sessionId = "session-lock";

        boolean firstLock =
                redisReissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(2));
        boolean secondLock =
                redisReissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(2));

        assertThat(firstLock).isTrue();
        assertThat(secondLock).isFalse();

        final boolean[] thirdLock = new boolean[1];
        waitUntil(
                () -> {
                    thirdLock[0] =
                            redisReissueLockStore.tryAcquireBySessionId(
                                    sessionId, Duration.ofSeconds(2));
                    return thirdLock[0];
                });

        assertThat(thirdLock[0]).isTrue();
    }

    @Test
    void releaseLockAllowsImmediateReacquire() {
        String sessionId = "session-lock-release";

        boolean firstLock =
                redisReissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(10));
        assertThat(firstLock).isTrue();

        redisReissueLockStore.releaseBySessionId(sessionId);

        boolean secondLock =
                redisReissueLockStore.tryAcquireBySessionId(sessionId, Duration.ofSeconds(10));
        assertThat(secondLock).isTrue();
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
