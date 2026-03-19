package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.time.Duration;
import java.time.Instant;
import java.util.Optional;

public interface RefreshTokenStore {
    void save(
            String sessionId,
            String refreshToken,
            String tokenId,
            Long userId,
            Duration timeToLive);

    Optional<StoredRefreshToken> findBySessionId(String sessionId);

    boolean matches(String sessionId, String refreshToken);

    void deleteBySessionId(String sessionId);

    void invalidateSession(String sessionId);

    void blacklistRefreshToken(String tokenId, Duration timeToLive);

    boolean isRefreshTokenBlacklisted(String tokenId);

    void blacklistAccessToken(String tokenId, Duration timeToLive);

    boolean isAccessTokenBlacklisted(String tokenId);

    Duration resolveTimeToLive(Instant expiresAt);
}
