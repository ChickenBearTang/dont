package com.ssafy.edu.awesomeproject.domain.notification.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class NotificationException extends CommonException {
    public NotificationException(ErrorCode errorCode) {
        super(errorCode);
    }

    public NotificationException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
