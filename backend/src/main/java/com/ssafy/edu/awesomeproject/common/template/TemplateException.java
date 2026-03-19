package com.ssafy.edu.awesomeproject.common.template;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.error.ErrorCode;

public class TemplateException extends CommonException {

    public TemplateException(ErrorCode errorCode) {
        super(errorCode);
    }

    public TemplateException(ErrorCode errorCode, Object details) {
        super(errorCode, details);
    }
}
