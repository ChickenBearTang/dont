package com.ssafy.edu.awesomeproject.common.config;

import com.ssafy.edu.awesomeproject.common.security.web.AdminAuthorizationInterceptor;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserIdArgumentResolver;
import com.ssafy.edu.awesomeproject.common.security.web.CurrentUserInterceptor;
import java.util.List;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    private final CurrentUserInterceptor currentUserInterceptor;
    private final AdminAuthorizationInterceptor adminAuthorizationInterceptor;
    private final CurrentUserIdArgumentResolver currentUserIdArgumentResolver;

    public WebMvcConfig(
            CurrentUserInterceptor currentUserInterceptor,
            AdminAuthorizationInterceptor adminAuthorizationInterceptor,
            CurrentUserIdArgumentResolver currentUserIdArgumentResolver) {
        this.currentUserInterceptor = currentUserInterceptor;
        this.adminAuthorizationInterceptor = adminAuthorizationInterceptor;
        this.currentUserIdArgumentResolver = currentUserIdArgumentResolver;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(currentUserInterceptor);
        registry.addInterceptor(adminAuthorizationInterceptor);
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(currentUserIdArgumentResolver);
    }
}
