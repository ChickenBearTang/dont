package com.ssafy.edu.awesomeproject.common.security.web;

import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class SignupRequestSizeInterceptor implements HandlerInterceptor {

    private final long maxSignupRequestBytes;

    public SignupRequestSizeInterceptor(
            @Value("${security.signup.max-request-bytes:8192}") long maxSignupRequestBytes) {
        this.maxSignupRequestBytes = maxSignupRequestBytes;
    }

    @Override
    public boolean preHandle(
            HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (!"POST".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        long contentLength = request.getContentLengthLong();
        if (contentLength < 0 || contentLength > maxSignupRequestBytes) {
            throw new CommonException(CommonErrorCode.PAYLOAD_TOO_LARGE);
        }

        return true;
    }
}
