package com.ssafy.edu.awesomeproject.domain.fin.consumption.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class ConsumptionException extends CommonException {
    public ConsumptionException(ErrorCode errorCode) {
        super(errorCode);
    }

    public ConsumptionException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
