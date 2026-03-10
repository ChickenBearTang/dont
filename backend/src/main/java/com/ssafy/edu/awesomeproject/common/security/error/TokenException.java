package com.ssafy.edu.awesomeproject.common.security.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class TokenException extends CommonException {
    public TokenException(ErrorCode errorCode) {
        super(errorCode);
    }

    public TokenException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
