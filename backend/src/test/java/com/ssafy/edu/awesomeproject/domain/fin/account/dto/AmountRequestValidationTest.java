package com.ssafy.edu.awesomeproject.domain.fin.account.dto;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertTimeout;

import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.ManualSavingsRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.MockDepositRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import java.math.BigDecimal;
import java.time.Duration;
import org.junit.jupiter.api.Test;

/**
 * 금액 요청 본문의 크기 검증. 금액은 JSON 에서 BigDecimal 로 그대로 들어오는데 "1E+999999999" 같은 짧은 지수 표기는 값이
 * 아주 크다. 컨트롤러 경계(Bean Validation)에서 값을 펼치지 않고 거절해야 한다.
 */
class AmountRequestValidationTest {

    private static final Validator VALIDATOR = Validation.buildDefaultValidatorFactory().getValidator();

    private static final String[] TOO_BIG = {"1E+999999999", "1E+4000000", "10000000000000", "99999999999999.99"};
    private static final String[] FINE = {"1", "5000", "5000.00", "9999999999999", "1E+3", "9999999999999.99"};

    @Test
    void depositAmountsAreBoundedWithoutExpandingThem() {
        for (String raw : TOO_BIG) {
            assertThat(violations(new MockDepositRequest(new BigDecimal(raw), null, null)))
                    .as("deposit %s", raw)
                    .isNotZero();
        }
        for (String raw : FINE) {
            assertThat(violations(new MockDepositRequest(new BigDecimal(raw), null, null)))
                    .as("deposit %s", raw)
                    .isZero();
        }
    }

    @Test
    void manualSavingsAmountsAreBounded() {
        for (String raw : TOO_BIG) {
            assertThat(violations(new ManualSavingsRequest(new BigDecimal(raw), "pw")))
                    .as("manual savings %s", raw)
                    .isNotZero();
        }
        for (String raw : FINE) {
            assertThat(violations(new ManualSavingsRequest(new BigDecimal(raw), "pw")))
                    .as("manual savings %s", raw)
                    .isZero();
        }
    }

    @Test
    void savingsRuleAmountAndKeywordAreBounded() {
        for (String raw : TOO_BIG) {
            assertThat(violations(rule(new BigDecimal(raw), "월급")))
                    .as("savings rule %s", raw)
                    .isNotZero();
        }
        assertThat(violations(rule(new BigDecimal("30000"), "월급"))).isZero();
        assertThat(violations(rule(BigDecimal.ZERO, "월급"))).isZero(); // 0원은 "옮길 게 없는 규칙"으로 허용돼 있다
        assertThat(violations(rule(new BigDecimal("30000"), "가".repeat(101)))).isNotZero(); // 열 길이 100
        assertThat(violations(rule(new BigDecimal("30000"), "가".repeat(100)))).isZero();
    }

    private static SavingsSettingRequest rule(BigDecimal amount, String keyword) {
        return SavingsSettingRequest.builder()
                .primaryAccountId(1L)
                .saveboxAccountId(2L)
                .keyword(keyword)
                .savingsAmount(amount)
                .isActive(true)
                .build();
    }

    private static int violations(Object request) {
        int[] count = new int[1];
        // 검증 자체가 값을 펼치면 오래 걸린다. 1초 안에 끝나야 한다.
        assertTimeout(Duration.ofSeconds(1), () -> count[0] = VALIDATOR.validate(request).size());
        return count[0];
    }
}
