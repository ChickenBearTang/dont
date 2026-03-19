package com.ssafy.edu.awesomeproject.domain.community.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class CommunityException extends CommonException {
    public CommunityException(ErrorCode errorCode) {
        super(errorCode);
    }

    public CommunityException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
