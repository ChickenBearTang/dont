package com.ssafy.edu.awesomeproject.domain.auth.cookie;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockCookie;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

class RefreshTokenCookieServiceTest {

    @Test
    void setAndResolveRefreshTokenCookie() {
        RefreshTokenCookieService service = new RefreshTokenCookieService(defaultProperties());
        MockHttpServletResponse response = new MockHttpServletResponse();

        service.setRefreshToken(response, "refresh-token", Duration.ofMinutes(10));

        String setCookie = response.getHeader("Set-Cookie");
        assertThat(setCookie).contains("__Host-refresh=refresh-token");
        assertThat(setCookie).contains("HttpOnly");
        assertThat(setCookie).contains("Secure");
        assertThat(setCookie).contains("Path=/");
        assertThat(setCookie).contains("SameSite=Lax");

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setCookies(new MockCookie("__Host-refresh", "refresh-token"));

        assertThat(service.resolveRefreshToken(request)).contains("refresh-token");
    }

    @Test
    void clearRefreshTokenCookieSetsExpiredCookie() {
        RefreshTokenCookieService service = new RefreshTokenCookieService(defaultProperties());
        MockHttpServletResponse response = new MockHttpServletResponse();

        service.clearRefreshToken(response);

        String setCookie = response.getHeader("Set-Cookie");
        assertThat(setCookie).contains("__Host-refresh=");
        assertThat(setCookie).contains("Max-Age=0");
    }

    private RefreshTokenCookieProperties defaultProperties() {
        return new RefreshTokenCookieProperties("__Host-refresh", "/", true, "Lax");
    }

    @Test
    void hostCookieRequiresSecureAndRootPath() {
        assertThatThrownBy(
                        () ->
                                new RefreshTokenCookieProperties(
                                        "__Host-refresh", "/auth", true, "Lax"))
                .isInstanceOf(IllegalStateException.class);

        assertThatThrownBy(
                        () -> new RefreshTokenCookieProperties("__Host-refresh", "/", false, "Lax"))
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void sameSiteNoneRequiresSecure() {
        assertThatThrownBy(() -> new RefreshTokenCookieProperties("refresh", "/", false, "None"))
                .isInstanceOf(IllegalStateException.class);
    }
}
