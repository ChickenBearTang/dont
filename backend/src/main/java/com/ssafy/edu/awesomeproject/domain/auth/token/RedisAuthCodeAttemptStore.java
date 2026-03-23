package com.ssafy.edu.awesomeproject.domain.auth.token;

import com.ssafy.edu.awesomeproject.domain.auth.service.AuthCodePurpose;
import java.time.Duration;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class RedisAuthCodeAttemptStore implements AuthCodeAttemptStore {
    private static final String KEY_PREFIX = "auth:code-attempt:";

    private final StringRedisTemplate stringRedisTemplate;

    public RedisAuthCodeAttemptStore(StringRedisTemplate stringRedisTemplate) {
        this.stringRedisTemplate = stringRedisTemplate;
    }

    @Override
    public long incrementSendAttempts(AuthCodePurpose purpose, String email, Duration timeToLive) {
        return increment(counterKey(purpose, "send", email), timeToLive);
    }

    @Override
    public long incrementVerifyAttempts(
            AuthCodePurpose purpose, String email, Duration timeToLive) {
        return increment(counterKey(purpose, "verify", email), timeToLive);
    }

    @Override
    public void clearVerifyAttempts(AuthCodePurpose purpose, String email) {
        stringRedisTemplate.delete(counterKey(purpose, "verify", email));
    }

    private long increment(String key, Duration timeToLive) {
        Long value = stringRedisTemplate.opsForValue().increment(key);
        if (value == null) {
            return 0L;
        }

        if (value == 1L) {
            stringRedisTemplate.expire(key, timeToLive);
        }

        return value;
    }

    private String counterKey(AuthCodePurpose purpose, String type, String email) {
        return KEY_PREFIX + purpose.key() + ":" + type + ":" + email;
    }
}
