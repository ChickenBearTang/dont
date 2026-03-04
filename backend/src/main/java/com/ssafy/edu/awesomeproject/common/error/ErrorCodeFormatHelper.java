package com.ssafy.edu.awesomeproject.common.error;

import java.util.regex.Pattern;

public final class ErrorCodeFormatHelper {
    private static final Pattern ERROR_CODE_PATTERN =
            Pattern.compile("^[A-Z][A-Z0-9]*_[1-5]\\d{2}_[1-9]\\d*$");

    private ErrorCodeFormatHelper() {}

    public static boolean isValidFormat(String errorCode) {
        if (errorCode == null) {
            return false;
        }
        return ERROR_CODE_PATTERN.matcher(errorCode).matches();
    }
}
