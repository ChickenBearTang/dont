package com.ssafy.edu.awesomeproject.common.error;

import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(CommonException.class)
    public ResponseEntity<CommonResponse<Object>> handleCommonException(CommonException ex) {
        ErrorCode errorCode = ex.getErrorCode();

        log.error(
            "CommonException occurred. code={}, details={}",
            errorCode.code(),
            ex.getDetails(),
            ex);

        return ResponseEntity.status(errorCode.status())
            .body(CommonResponse.fail(errorCode, ex.getDetails()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<CommonResponse<List<ValidationError>>> handleValidationException(
        MethodArgumentNotValidException ex) {
        List<ValidationError> errors =
            ex.getBindingResult().getFieldErrors().stream()
                .map(this::toValidationError)
                .toList();

        log.error("MethodArgumentNotValidException occurred. errors={}", errors, ex);

        return ResponseEntity.status(CommonErrorCode.VALIDATION_FAILED.status())
            .body(CommonResponse.fail(CommonErrorCode.VALIDATION_FAILED, errors));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<CommonResponse<List<String>>> handleConstraintViolation(
        ConstraintViolationException ex) {
        List<String> errors =
            ex.getConstraintViolations().stream()
                .map(
                    violation ->
                        violation.getPropertyPath() + ": " + violation.getMessage())
                .toList();

        log.error("ConstraintViolationException occurred. errors={}", errors, ex);

        return ResponseEntity.status(CommonErrorCode.VALIDATION_FAILED.status())
            .body(CommonResponse.fail(CommonErrorCode.VALIDATION_FAILED, errors));
    }


    @ExceptionHandler(Exception.class)
    public ResponseEntity<?> handleUnexpected(Exception ex, HttpServletRequest request)
        throws Exception {
        String accept = request.getHeader("Accept");

        if (accept != null && accept.contains("text/event-stream")) {
            throw ex;
        }

        log.error(
            "Unexpected exception occurred. method={}, uri={}, queryString={}",
            request.getMethod(),
            request.getRequestURI(),
            request.getQueryString(),
            ex);

        return ResponseEntity.status(CommonErrorCode.INTERNAL_SERVER_ERROR.status())
            .body(CommonResponse.fail(CommonErrorCode.INTERNAL_SERVER_ERROR));
    }

    private ValidationError toValidationError(FieldError fieldError) {
        return new ValidationError(fieldError.getField(), fieldError.getDefaultMessage());
    }
}
