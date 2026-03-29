package com.ssafy.edu.awesomeproject.common.s3.error;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class S3Exception extends CommonException {
    public S3Exception(ErrorCode errorCode) {
        super(errorCode);
    }

    public S3Exception(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
