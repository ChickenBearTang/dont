package com.ssafy.edu.awesomeproject.domain.auth.cookie;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.time.Duration;
import java.util.Arrays;
import java.util.Optional;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;

@Component
public class RefreshTokenCookieService {
    private final RefreshTokenCookieProperties properties;

    public RefreshTokenCookieService(RefreshTokenCookieProperties properties) {
        this.properties = properties;
    }

    public void setRefreshToken(
            HttpServletResponse response, String refreshToken, Duration timeToLive) {
        ResponseCookie cookie =
                ResponseCookie.from(properties.cookieName(), refreshToken)
                        .httpOnly(true)
                        .secure(properties.secure())
                        .sameSite(properties.sameSite())
                        .path(properties.path())
                        .maxAge(timeToLive)
                        .build();

        response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
    }

    public void clearRefreshToken(HttpServletResponse response) {
        ResponseCookie cookie =
                ResponseCookie.from(properties.cookieName(), "")
                        .httpOnly(true)
                        .secure(properties.secure())
                        .sameSite(properties.sameSite())
                        .path(properties.path())
                        .maxAge(Duration.ZERO)
                        .build();

        response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
    }

    public Optional<String> resolveRefreshToken(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null || cookies.length == 0) {
            return Optional.empty();
        }

        return Arrays.stream(cookies)
                .filter(cookie -> properties.cookieName().equals(cookie.getName()))
                .map(Cookie::getValue)
                .filter(value -> value != null && !value.isBlank())
                .findFirst();
    }
}
