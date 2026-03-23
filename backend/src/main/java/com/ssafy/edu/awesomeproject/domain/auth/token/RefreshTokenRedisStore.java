package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class RefreshTokenRedisStore implements RefreshTokenStore {
    private static final String REFRESH_KEY_PREFIX = "rt:";
    private static final String REFRESH_BLACKLIST_KEY_PREFIX = "bl:rt:";
    private static final String ACCESS_BLACKLIST_KEY_PREFIX = "bl:at:";

    private static final String TOKEN_HASH_FIELD = "tokenHash";
    private static final String TOKEN_ID_FIELD = "jti";
    private static final String USER_ID_FIELD = "uid";

    private final StringRedisTemplate stringRedisTemplate;
    private final RefreshTokenHashService refreshTokenHashService;
    private final TokenTimeToLiveResolver tokenTimeToLiveResolver;

    public RefreshTokenRedisStore(
            StringRedisTemplate stringRedisTemplate,
            RefreshTokenHashService refreshTokenHashService,
            TokenTimeToLiveResolver tokenTimeToLiveResolver) {
        this.stringRedisTemplate = stringRedisTemplate;
        this.refreshTokenHashService = refreshTokenHashService;
        this.tokenTimeToLiveResolver = tokenTimeToLiveResolver;
    }

    @Override
    public void save(
            String sessionId,
            String refreshToken,
            String tokenId,
            Long userId,
            Duration timeToLive) {
        if (!hasPositiveTimeToLive(timeToLive)) {
            deleteBySessionId(sessionId);
            return;
        }

        String refreshKey = refreshKey(sessionId);

        stringRedisTemplate
                .opsForHash()
                .put(refreshKey, TOKEN_HASH_FIELD, refreshTokenHashService.hash(refreshToken));
        stringRedisTemplate.opsForHash().put(refreshKey, TOKEN_ID_FIELD, tokenId);
        stringRedisTemplate.opsForHash().put(refreshKey, USER_ID_FIELD, String.valueOf(userId));
        stringRedisTemplate.expire(refreshKey, timeToLive);
    }

    @Override
    public Optional<StoredRefreshToken> findBySessionId(String sessionId) {
        String refreshKey = refreshKey(sessionId);
        Object tokenHash = stringRedisTemplate.opsForHash().get(refreshKey, TOKEN_HASH_FIELD);
        Object tokenId = stringRedisTemplate.opsForHash().get(refreshKey, TOKEN_ID_FIELD);
        Object userId = stringRedisTemplate.opsForHash().get(refreshKey, USER_ID_FIELD);

        if (!(tokenHash instanceof String tokenHashValue)
                || !(tokenId instanceof String tokenIdValue)
                || !(userId instanceof String userIdValue)) {
            return Optional.empty();
        }

        return Optional.of(
                new StoredRefreshToken(tokenHashValue, tokenIdValue, Long.valueOf(userIdValue)));
    }

    @Override
    public boolean matches(String sessionId, String refreshToken) {
        return findBySessionId(sessionId)
                .map(
                        storedRefreshToken ->
                                MessageDigest.isEqual(
                                        storedRefreshToken
                                                .tokenHash()
                                                .getBytes(StandardCharsets.UTF_8),
                                        refreshTokenHashService
                                                .hash(refreshToken)
                                                .getBytes(StandardCharsets.UTF_8)))
                .orElse(false);
    }

    @Override
    public void deleteBySessionId(String sessionId) {
        stringRedisTemplate.delete(refreshKey(sessionId));
    }

    @Override
    public void deleteByUserId(Long userId) {
        Set<String> keys = stringRedisTemplate.keys(REFRESH_KEY_PREFIX + "*");
        if (keys == null || keys.isEmpty()) {
            return;
        }

        String targetUserId = String.valueOf(userId);
        for (String key : keys) {
            Object uid = stringRedisTemplate.opsForHash().get(key, USER_ID_FIELD);
            if (targetUserId.equals(uid)) {
                stringRedisTemplate.delete(key);
            }
        }
    }

    @Override
    public void invalidateSession(String sessionId) {
        deleteBySessionId(sessionId);
    }

    @Override
    public void blacklistRefreshToken(String tokenId, Duration timeToLive) {
        writeBlacklistEntry(refreshBlacklistKey(tokenId), timeToLive);
    }

    @Override
    public boolean isRefreshTokenBlacklisted(String tokenId) {
        return stringRedisTemplate.hasKey(refreshBlacklistKey(tokenId));
    }

    @Override
    public void blacklistAccessToken(String tokenId, Duration timeToLive) {
        writeBlacklistEntry(accessBlacklistKey(tokenId), timeToLive);
    }

    @Override
    public boolean isAccessTokenBlacklisted(String tokenId) {
        return stringRedisTemplate.hasKey(accessBlacklistKey(tokenId));
    }

    @Override
    public Duration resolveTimeToLive(Instant expiresAt) {
        return tokenTimeToLiveResolver.resolve(expiresAt);
    }

    private void writeBlacklistEntry(String key, Duration timeToLive) {
        if (!hasPositiveTimeToLive(timeToLive)) {
            stringRedisTemplate.delete(key);
            return;
        }

        stringRedisTemplate.opsForValue().set(key, "1", timeToLive);
    }

    private boolean hasPositiveTimeToLive(Duration timeToLive) {
        return timeToLive != null && !timeToLive.isNegative() && !timeToLive.isZero();
    }

    private String refreshKey(String sessionId) {
        return REFRESH_KEY_PREFIX + sessionId;
    }

    private String refreshBlacklistKey(String tokenId) {
        return REFRESH_BLACKLIST_KEY_PREFIX + tokenId;
    }

    private String accessBlacklistKey(String tokenId) {
        return ACCESS_BLACKLIST_KEY_PREFIX + tokenId;
    }

    long getTimeToLiveSeconds(String key) {
        Long ttl = stringRedisTemplate.getExpire(key, TimeUnit.SECONDS);
        return ttl == null ? -2L : ttl;
    }
}
