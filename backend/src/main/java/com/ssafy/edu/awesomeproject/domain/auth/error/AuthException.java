package com.ssafy.edu.awesomeproject.domain.auth.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class AuthException extends CommonException {
    public AuthException(ErrorCode errorCode) {
        super(errorCode);
    }

    public AuthException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
