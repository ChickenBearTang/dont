package com.ssafy.edu.awesomeproject.common.config;

import com.ssafy.edu.awesomeproject.common.security.web.AdminAuthorizationInterceptor;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserIdArgumentResolver;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserInterceptor;
import com.ssafy.edu.awesomeproject.common.security.web.SignupRequestSizeInterceptor;
import java.util.Arrays;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    private static final String[] DEFAULT_ALLOWED_ORIGIN_PATTERNS = {
        "http://localhost:5173", "http://127.0.0.1:5173"
    };

    private final CurrentUserInterceptor currentUserInterceptor;
    private final AdminAuthorizationInterceptor adminAuthorizationInterceptor;
    private final CurrentUserIdArgumentResolver currentUserIdArgumentResolver;
    private final SignupRequestSizeInterceptor signupRequestSizeInterceptor;
    private final String corsAllowedOriginPatterns;

    public WebMvcConfig(
            CurrentUserInterceptor currentUserInterceptor,
            AdminAuthorizationInterceptor adminAuthorizationInterceptor,
            CurrentUserIdArgumentResolver currentUserIdArgumentResolver,
            SignupRequestSizeInterceptor signupRequestSizeInterceptor,
            @Value(
                            "${security.cors.allowed-origin-patterns:http://localhost:5173,http://127.0.0.1:5173}")
                    String corsAllowedOriginPatterns) {
        this.currentUserInterceptor = currentUserInterceptor;
        this.adminAuthorizationInterceptor = adminAuthorizationInterceptor;
        this.currentUserIdArgumentResolver = currentUserIdArgumentResolver;
        this.signupRequestSizeInterceptor = signupRequestSizeInterceptor;
        this.corsAllowedOriginPatterns = corsAllowedOriginPatterns;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(currentUserInterceptor);
        registry.addInterceptor(signupRequestSizeInterceptor).addPathPatterns("/auth/signup");
        registry.addInterceptor(adminAuthorizationInterceptor);
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns(resolveAllowedOriginPatterns())
                .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }

    private String[] resolveAllowedOriginPatterns() {
        String[] configuredPatterns =
                Arrays.stream(corsAllowedOriginPatterns.split(","))
                        .map(String::trim)
                        .filter(pattern -> !pattern.isEmpty())
                        .filter(pattern -> !"*".equals(pattern))
                        .toArray(String[]::new);

        if (configuredPatterns.length == 0) {
            return DEFAULT_ALLOWED_ORIGIN_PATTERNS;
        }

        return configuredPatterns;
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(currentUserIdArgumentResolver);
    }
}
