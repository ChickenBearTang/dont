package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.time.Duration;
import java.util.Optional;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class RedisPasswordResetTokenStore implements PasswordResetTokenStore {
    private static final String CODE_KEY_PREFIX = "pr:code:";

    private final StringRedisTemplate stringRedisTemplate;

    public RedisPasswordResetTokenStore(StringRedisTemplate stringRedisTemplate) {
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

    private String codeKey(String email) {
        return CODE_KEY_PREFIX + email;
    }
}
