package com.ssafy.edu.awesomeproject.domain.user.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class UserException extends CommonException {
    public UserException(ErrorCode errorCode) {
        super(errorCode);
    }

    public UserException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
