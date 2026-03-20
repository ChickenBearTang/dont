package com.ssafy.edu.awesomeproject.domain.fin.account.error;

import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice(basePackages = "com.ssafy.edu.awesomeproject.domain.fin.account.controller")
public class AccountExceptionHandler {

    @ExceptionHandler(AccountException.class)
    public ResponseEntity<AccountApiResponse<Void>> handleAccountException(AccountException e) {
        log.error("Account 도메인 예외 발생: [{}] {}", e.getErrorCode().code(), e.getMessage());
        return ResponseEntity.status(e.getErrorCode().status())
                .body(AccountApiResponse.error(e.getErrorCode().code(), e.getMessage()));
    }
}
