package com.ssafy.edu.awesomeproject.domain.auth.cookie;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class RefreshTokenCookieProperties {
    private final String cookieName;
    private final String path;
    private final boolean secure;
    private final String sameSite;

    public RefreshTokenCookieProperties(
            @Value("${auth.jwt.refresh-cookie.name}") String cookieName,
            @Value("${auth.jwt.refresh-cookie.path}") String path,
            @Value("${auth.jwt.refresh-cookie.secure}") boolean secure,
            @Value("${auth.jwt.refresh-cookie.same-site}") String sameSite) {
        validate(cookieName, path, secure, sameSite);
        this.cookieName = cookieName;
        this.path = path;
        this.secure = secure;
        this.sameSite = sameSite;
    }

    private void validate(String cookieName, String path, boolean secure, String sameSite) {
        if (cookieName.startsWith("__Host-") && !secure) {
            throw new IllegalStateException("__Host- 쿠키는 secure=true를 사용해야 합니다.");
        }

        if (cookieName.startsWith("__Host-") && !"/".equals(path)) {
            throw new IllegalStateException("__Host- 쿠키는 path=/를 사용해야 합니다.");
        }

        if ("None".equalsIgnoreCase(sameSite) && !secure) {
            throw new IllegalStateException("SameSite=None 쿠키는 secure=true를 사용해야 합니다.");
        }
    }

    public String cookieName() {
        return cookieName;
    }

    public String path() {
        return path;
    }

    public boolean secure() {
        return secure;
    }

    public String sameSite() {
        return sameSite;
    }
}
