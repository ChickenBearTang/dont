package com.ssafy.edu.awesomeproject.domain.auth.service;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.mock.web.MockHttpServletRequest;

@ExtendWith(MockitoExtension.class)
class AuthRateLimitServiceTest {

    @Mock private StringRedisTemplate stringRedisTemplate;

    @Mock private ValueOperations<String, String> valueOperations;

    private AuthRateLimitService authRateLimitService;

    @BeforeEach
    void setUp() {
        authRateLimitService =
                new AuthRateLimitService(
                        stringRedisTemplate,
                        2,
                        2,
                        900L,
                        3,
                        60L,
                        "127.0.0.1,::1");
    }

    @Test
    void validateLoginAllowedThrowsWhenIpLimitExceeded() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("rl:auth:login:ip:127.0.0.1")).thenReturn("2");

        assertThatThrownBy(() -> authRateLimitService.validateLoginAllowed("test@example.com", "127.0.0.1"))
                .isInstanceOfSatisfying(
                        AuthException.class,
                        exception ->
                                org.assertj.core.api.Assertions.assertThat(exception.getErrorCode())
                                        .isEqualTo(AuthErrorCode.TOO_MANY_REQUESTS));
    }

    @Test
    void recordLoginFailureIncrementsEmailAndIpBuckets() {
        when(stringRedisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.increment(any())).thenReturn(1L);

        authRateLimitService.recordLoginFailure("TeSt@Example.com", "127.0.0.1");

        verify(valueOperations).increment("rl:auth:login:ip:127.0.0.1");
        verify(valueOperations).increment("rl:auth:login:email:test@example.com");
        verify(stringRedisTemplate).expire(eq("rl:auth:login:ip:127.0.0.1"), any());
        verify(stringRedisTemplate).expire(eq("rl:auth:login:email:test@example.com"), any());
    }

    @Test
    void resolveClientIpUsesForwardedHeaderWhenRequestComesFromTrustedProxy() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Forwarded-For", "198.51.100.10, 127.0.0.1");
        request.setRemoteAddr("127.0.0.1");

        String clientIp = authRateLimitService.resolveClientIp(request);

        org.assertj.core.api.Assertions.assertThat(clientIp).isEqualTo("198.51.100.10");
    }

    @Test
    void resolveClientIpSkipsTrustedProxyIpsInForwardedChain() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Forwarded-For", "203.0.113.77, 198.51.100.10, 127.0.0.1");
        request.setRemoteAddr("127.0.0.1");

        String clientIp = authRateLimitService.resolveClientIp(request);

        org.assertj.core.api.Assertions.assertThat(clientIp).isEqualTo("198.51.100.10");
    }

    @Test
    void resolveClientIpIgnoresForwardedHeaderWhenProxyIsUntrusted() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Forwarded-For", "198.51.100.10, 203.0.113.5");
        request.setRemoteAddr("203.0.113.5");

        String clientIp = authRateLimitService.resolveClientIp(request);

        org.assertj.core.api.Assertions.assertThat(clientIp).isEqualTo("203.0.113.5");
    }

    @Test
    void resolveClientIpUsesForwardedHeaderWhenRemoteAddrMatchesTrustedProxyCidr() {
        AuthRateLimitService cidrAwareService =
                new AuthRateLimitService(
                        stringRedisTemplate,
                        2,
                        2,
                        900L,
                        3,
                        60L,
                        "127.0.0.1,::1,172.18.0.0/16");

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Forwarded-For", "198.51.100.10, 172.18.0.4");
        request.setRemoteAddr("172.18.0.4");

        String clientIp = cidrAwareService.resolveClientIp(request);

        org.assertj.core.api.Assertions.assertThat(clientIp).isEqualTo("198.51.100.10");
    }
}
