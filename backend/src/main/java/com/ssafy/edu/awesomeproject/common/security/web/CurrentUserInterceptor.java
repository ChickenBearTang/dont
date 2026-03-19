package com.ssafy.edu.awesomeproject.common.security.web;

import com.ssafy.edu.awesomeproject.common.annotation.AdminOnly;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.lang.reflect.Parameter;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class CurrentUserInterceptor implements HandlerInterceptor {
    public static final String CURRENT_USER_ID_ATTR = "currentUserId";
    public static final String CURRENT_USER_ROLE_ATTR = "currentUserRole";

    private final CurrentUserExtractor currentUserExtractor;

    public CurrentUserInterceptor(CurrentUserExtractor currentUserExtractor) {
        this.currentUserExtractor = currentUserExtractor;
    }

    @Override
    public boolean preHandle(
            HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (!(handler instanceof HandlerMethod handlerMethod)) {
            return true;
        }

        if (!requiresAuthentication(handlerMethod)) {
            return true;
        }

        CurrentUserExtractor.CurrentUserAuth auth =
                currentUserExtractor.extractAuthFromRequestHeader(request);
        request.setAttribute(CURRENT_USER_ID_ATTR, auth.userId());
        request.setAttribute(CURRENT_USER_ROLE_ATTR, auth.role());
        return true;
    }

    private boolean requiresAuthentication(HandlerMethod handlerMethod) {
        if (handlerMethod.hasMethodAnnotation(AdminOnly.class)
                || handlerMethod.getBeanType().isAnnotationPresent(AdminOnly.class)) {
            return true;
        }

        for (Parameter parameter : handlerMethod.getMethod().getParameters()) {
            if (parameter.isAnnotationPresent(CurrentUserId.class)) {
                return true;
            }
        }
        return false;
    }
}
