package com.ssafy.edu.awesomeproject.common.config;

import com.ssafy.edu.awesomeproject.common.security.web.AdminAuthorizationInterceptor;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserIdArgumentResolver;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserInterceptor;
import com.ssafy.edu.awesomeproject.common.security.web.SignupRequestSizeInterceptor;
import java.util.List;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    private final CurrentUserInterceptor currentUserInterceptor;
    private final AdminAuthorizationInterceptor adminAuthorizationInterceptor;
    private final CurrentUserIdArgumentResolver currentUserIdArgumentResolver;
    private final SignupRequestSizeInterceptor signupRequestSizeInterceptor;

    public WebMvcConfig(
            CurrentUserInterceptor currentUserInterceptor,
            AdminAuthorizationInterceptor adminAuthorizationInterceptor,
            CurrentUserIdArgumentResolver currentUserIdArgumentResolver,
            SignupRequestSizeInterceptor signupRequestSizeInterceptor) {
        this.currentUserInterceptor = currentUserInterceptor;
        this.adminAuthorizationInterceptor = adminAuthorizationInterceptor;
        this.currentUserIdArgumentResolver = currentUserIdArgumentResolver;
        this.signupRequestSizeInterceptor = signupRequestSizeInterceptor;
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
                .allowedOrigins("http://localhost:5173", "http://127.0.0.1:5173")
                .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(currentUserIdArgumentResolver);
    }
}
