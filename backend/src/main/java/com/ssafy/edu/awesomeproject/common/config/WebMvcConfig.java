package com.ssafy.edu.awesomeproject.common.config;

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
    private final CurrentUserIdArgumentResolver currentUserIdArgumentResolver;

    public WebMvcConfig(
            CurrentUserInterceptor currentUserInterceptor,
            CurrentUserIdArgumentResolver currentUserIdArgumentResolver) {
        this.currentUserInterceptor = currentUserInterceptor;
        this.currentUserIdArgumentResolver = currentUserIdArgumentResolver;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(currentUserInterceptor);
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(currentUserIdArgumentResolver);
    }
}

