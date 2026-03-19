package com.ssafy.edu.awesomeproject.domain.fin.account.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class AccountException extends CommonException {
    public AccountException(ErrorCode errorCode) {
        super(errorCode);
    }

    public AccountException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
