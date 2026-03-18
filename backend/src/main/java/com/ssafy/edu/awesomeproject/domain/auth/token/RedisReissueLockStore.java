package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.time.Duration;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class RedisReissueLockStore implements ReissueLockStore {
    private static final String REFRESH_LOCK_KEY_PREFIX = "lock:rt:";

    private final StringRedisTemplate stringRedisTemplate;

    public RedisReissueLockStore(StringRedisTemplate stringRedisTemplate) {
        this.stringRedisTemplate = stringRedisTemplate;
    }

    @Override
    public boolean tryAcquireBySessionId(String sessionId, Duration timeToLive) {
        if (!hasPositiveTimeToLive(timeToLive)) {
            return false;
        }

        Boolean locked =
                stringRedisTemplate
                        .opsForValue()
                        .setIfAbsent(refreshLockKey(sessionId), "1", timeToLive);
        return Boolean.TRUE.equals(locked);
    }

    @Override
    public void releaseBySessionId(String sessionId) {
        stringRedisTemplate.delete(refreshLockKey(sessionId));
    }

    private boolean hasPositiveTimeToLive(Duration timeToLive) {
        return timeToLive != null && !timeToLive.isNegative() && !timeToLive.isZero();
    }

    private String refreshLockKey(String sessionId) {
        return REFRESH_LOCK_KEY_PREFIX + sessionId;
    }
}
