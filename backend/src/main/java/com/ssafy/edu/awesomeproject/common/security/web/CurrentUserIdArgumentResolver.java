package com.ssafy.edu.awesomeproject.common.security.web;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.security.error.TokenErrorCode;
import com.ssafy.edu.awesomeproject.common.security.error.TokenException;
import org.springframework.core.MethodParameter;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

@Component
public class CurrentUserIdArgumentResolver implements HandlerMethodArgumentResolver {
    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        return parameter.hasParameterAnnotation(CurrentUserId.class)
                && (parameter.getParameterType().equals(Long.class)
                        || parameter.getParameterType().equals(long.class));
    }

    @Override
    public Object resolveArgument(
            MethodParameter parameter,
            ModelAndViewContainer mavContainer,
            NativeWebRequest webRequest,
            WebDataBinderFactory binderFactory) {
        Object userId =
                webRequest.getAttribute(
                        CurrentUserInterceptor.CURRENT_USER_ID_ATTR,
                        NativeWebRequest.SCOPE_REQUEST);
        if (userId == null) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }
        return userId;
    }
}
