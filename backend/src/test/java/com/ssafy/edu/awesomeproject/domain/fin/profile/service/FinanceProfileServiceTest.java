package com.ssafy.edu.awesomeproject.domain.fin.profile.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.profile.dto.response.FinanceProfileResponse;
import java.math.BigDecimal;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class FinanceProfileServiceTest {

    @Mock private AccountRepository accountRepository;

    @Mock private CardRepository cardRepository;

    @Mock private CardTransactionRepository cardTransactionRepository;

    private FinanceProfileService financeProfileService;

    @BeforeEach
    void setUp() {
        financeProfileService =
                new FinanceProfileService(accountRepository, cardRepository, cardTransactionRepository);
    }

    @Test
    void getFinanceProfileAggregatesBalancesAndCardAmount() {
        when(accountRepository.sumBalanceByUserId(1001L)).thenReturn(new BigDecimal("2500000"));
        when(accountRepository.sumBalanceByUserIdAndRole(1001L, AccountRole.SAVE_BOX))
                .thenReturn(new BigDecimal("700000"));
        when(cardTransactionRepository.sumAmountByUserIdAndDateRange(
                        org.mockito.ArgumentMatchers.eq(1001L),
                        org.mockito.ArgumentMatchers.any(),
                        org.mockito.ArgumentMatchers.any()))
                .thenReturn(320000L);
        when(cardRepository.findWithdrawalDatesByUserId(1001L))
                .thenReturn(List.of("15", "20261231"));

        FinanceProfileResponse response = financeProfileService.getFinanceProfile("U1001");

        assertThat(response.currentBalance()).isEqualTo(2_500_000.0);
        assertThat(response.emergencyFundBalance()).isEqualTo(700_000.0);
        assertThat(response.expectedCardPaymentAmount()).isEqualTo(320_000.0);
        assertThat(response.daysUntilCardDue()).isGreaterThanOrEqualTo(0);
        assertThat(response.daysUntilCardDue()).isLessThanOrEqualTo(370);
    }

    @Test
    void getFinanceProfileRejectsInvalidUserId() {
        assertThatThrownBy(() -> financeProfileService.getFinanceProfile("abc"))
                .isInstanceOf(NumberFormatException.class);
    }
}
