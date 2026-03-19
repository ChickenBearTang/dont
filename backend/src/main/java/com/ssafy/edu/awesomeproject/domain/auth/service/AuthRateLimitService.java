package com.ssafy.edu.awesomeproject.domain.auth.service;

import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import jakarta.servlet.http.HttpServletRequest;
import java.time.Duration;
import java.util.Arrays;
import java.util.Set;
import java.util.Locale;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
public class AuthRateLimitService {
    private static final Logger log = LoggerFactory.getLogger(AuthRateLimitService.class);

    private static final String LOGIN_IP_KEY_PREFIX = "rl:auth:login:ip:";
    private static final String LOGIN_EMAIL_KEY_PREFIX = "rl:auth:login:email:";
    private static final String REISSUE_IP_KEY_PREFIX = "rl:auth:reissue:ip:";

    private final StringRedisTemplate stringRedisTemplate;

    private final int loginMaxAttemptsPerIp;
    private final int loginMaxAttemptsPerEmail;
    private final Duration loginWindow;

    private final int reissueMaxAttemptsPerIp;
    private final Duration reissueWindow;
    private final Set<String> trustedProxyAddresses;

    public AuthRateLimitService(
            StringRedisTemplate stringRedisTemplate,
            @Value("${security.auth.login.max-attempts-per-ip:20}") int loginMaxAttemptsPerIp,
            @Value("${security.auth.login.max-attempts-per-email:10}") int loginMaxAttemptsPerEmail,
            @Value("${security.auth.login.window-seconds:900}") long loginWindowSeconds,
            @Value("${security.auth.reissue.max-attempts-per-ip:30}") int reissueMaxAttemptsPerIp,
            @Value("${security.auth.reissue.window-seconds:60}") long reissueWindowSeconds,
            @Value("${security.auth.trusted-proxies:127.0.0.1,::1}") String trustedProxies) {
        this.stringRedisTemplate = stringRedisTemplate;
        this.loginMaxAttemptsPerIp = loginMaxAttemptsPerIp;
        this.loginMaxAttemptsPerEmail = loginMaxAttemptsPerEmail;
        this.loginWindow = Duration.ofSeconds(loginWindowSeconds);
        this.reissueMaxAttemptsPerIp = reissueMaxAttemptsPerIp;
        this.reissueWindow = Duration.ofSeconds(reissueWindowSeconds);
        this.trustedProxyAddresses = parseTrustedProxies(trustedProxies);
    }

    public String resolveClientIp(HttpServletRequest request) {
        String remoteAddress = normalizeIp(request.getRemoteAddr());
        if (isTrustedProxy(remoteAddress)) {
            String candidateIp = resolveFromForwardedHeader(request.getHeader("X-Forwarded-For"));
            if (!"unknown".equals(candidateIp)) {
                return candidateIp;
            }
        }

        return remoteAddress;
    }

    public void validateLoginAllowed(String email, String clientIp) {
        if (isRateLimitExceeded(LOGIN_IP_KEY_PREFIX + normalize(clientIp), loginMaxAttemptsPerIp)
                || isRateLimitExceeded(
                        LOGIN_EMAIL_KEY_PREFIX + normalize(email), loginMaxAttemptsPerEmail)) {
            throw new AuthException(AuthErrorCode.TOO_MANY_REQUESTS);
        }
    }

    public void recordLoginFailure(String email, String clientIp) {
        incrementWithWindow(LOGIN_IP_KEY_PREFIX + normalize(clientIp), loginWindow);
        incrementWithWindow(LOGIN_EMAIL_KEY_PREFIX + normalize(email), loginWindow);
    }

    public void resetLoginFailures(String email) {
        safeDelete(LOGIN_EMAIL_KEY_PREFIX + normalize(email));
    }

    public void validateReissueAllowed(String clientIp) {
        if (isRateLimitExceeded(REISSUE_IP_KEY_PREFIX + normalize(clientIp), reissueMaxAttemptsPerIp)) {
            throw new AuthException(AuthErrorCode.TOO_MANY_REQUESTS);
        }
    }

    public void recordReissueAttempt(String clientIp) {
        incrementWithWindow(REISSUE_IP_KEY_PREFIX + normalize(clientIp), reissueWindow);
    }

    private boolean isRateLimitExceeded(String key, int maxAttempts) {
        try {
            String rawCount = stringRedisTemplate.opsForValue().get(key);
            if (rawCount == null) {
                return false;
            }

            return Long.parseLong(rawCount) >= maxAttempts;
        } catch (Exception exception) {
            log.warn("auth.ratelimit.read_failed key={}", key, exception);
            return false;
        }
    }

    private void incrementWithWindow(String key, Duration timeWindow) {
        try {
            Long count = stringRedisTemplate.opsForValue().increment(key);
            if (count != null && count == 1L) {
                stringRedisTemplate.expire(key, timeWindow);
            }
        } catch (Exception exception) {
            log.warn("auth.ratelimit.increment_failed key={}", key, exception);
        }
    }

    private void safeDelete(String key) {
        try {
            stringRedisTemplate.delete(key);
        } catch (Exception exception) {
            log.warn("auth.ratelimit.delete_failed key={}", key, exception);
        }
    }

    private String normalize(String rawValue) {
        if (rawValue == null) {
            return "unknown";
        }

        return rawValue.trim().toLowerCase(Locale.ROOT);
    }

    private boolean isTrustedProxy(String ipAddress) {
        return trustedProxyAddresses.contains(normalize(ipAddress));
    }

    private Set<String> parseTrustedProxies(String trustedProxies) {
        if (trustedProxies == null || trustedProxies.isBlank()) {
            return Set.of();
        }

        return Arrays.stream(trustedProxies.split(","))
                .map(this::normalize)
                .filter(value -> !"unknown".equals(value))
                .collect(Collectors.toUnmodifiableSet());
    }

    private String normalizeIp(String ipAddress) {
        return normalize(ipAddress);
    }

    private String resolveFromForwardedHeader(String forwardedFor) {
        if (forwardedFor == null || forwardedFor.isBlank()) {
            return "unknown";
        }

        String[] forwardedIps = forwardedFor.split(",");
        for (int index = forwardedIps.length - 1; index >= 0; index--) {
            String candidateIp = normalizeIp(forwardedIps[index]);
            if (!"unknown".equals(candidateIp) && !isTrustedProxy(candidateIp)) {
                return candidateIp;
            }
        }

        return "unknown";
    }
}
