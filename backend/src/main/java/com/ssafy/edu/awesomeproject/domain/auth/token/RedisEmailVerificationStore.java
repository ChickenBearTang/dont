package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class RedisEmailVerificationStore implements EmailVerificationStore {
    private static final String CODE_KEY_PREFIX = "ev:code:";
    private static final String VERIFIED_KEY_PREFIX = "ev:verified:";

    private final StringRedisTemplate stringRedisTemplate;

    public RedisEmailVerificationStore(StringRedisTemplate stringRedisTemplate) {
        this.stringRedisTemplate = stringRedisTemplate;
    }

    @Override
    public void saveCode(String email, String code, Duration timeToLive) {
        stringRedisTemplate.opsForValue().set(codeKey(email), code, timeToLive);
    }

    @Override
    public Optional<String> findCode(String email) {
        return Optional.ofNullable(stringRedisTemplate.opsForValue().get(codeKey(email)));
    }

    @Override
    public void removeCode(String email) {
        stringRedisTemplate.delete(codeKey(email));
    }

    @Override
    public void markVerified(String email, Duration timeToLive) {
        stringRedisTemplate.opsForValue().set(verifiedKey(email), "1", timeToLive);
    }

    @Override
    public boolean isVerified(String email) {
        return Boolean.TRUE.equals(stringRedisTemplate.hasKey(verifiedKey(email)));
    }

    @Override
    public void clearVerified(String email) {
        stringRedisTemplate.delete(verifiedKey(email));
    }

    long getTimeToLiveSeconds(String key) {
        Long ttl = stringRedisTemplate.getExpire(key, TimeUnit.SECONDS);
        return ttl == null ? -2L : ttl;
    }

    private String codeKey(String email) {
        return CODE_KEY_PREFIX + email;
    }

    private String verifiedKey(String email) {
        return VERIFIED_KEY_PREFIX + email;
    }
}
