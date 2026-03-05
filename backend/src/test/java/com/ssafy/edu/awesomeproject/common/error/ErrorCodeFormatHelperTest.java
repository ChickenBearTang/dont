package com.ssafy.edu.awesomeproject.common.error;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class ErrorCodeFormatHelperTest {

    @Test
    void isValidFormat_whenCodeMatchesConvention_returnsTrue() {
        assertThat(ErrorCodeFormatHelper.isValidFormat("COMMON_400_1")).isTrue();
        assertThat(ErrorCodeFormatHelper.isValidFormat("AUTH2_500_12")).isTrue();
    }

    @Test
    void isValidFormat_whenCodeIsNullOrInvalid_returnsFalse() {
        assertThat(ErrorCodeFormatHelper.isValidFormat(null)).isFalse();
        assertThat(ErrorCodeFormatHelper.isValidFormat("common_400_1")).isFalse();
        assertThat(ErrorCodeFormatHelper.isValidFormat("COMMON_600_1")).isFalse();
        assertThat(ErrorCodeFormatHelper.isValidFormat("COMMON_400_0")).isFalse();
        assertThat(ErrorCodeFormatHelper.isValidFormat("COMMON400_1")).isFalse();
    }
}
