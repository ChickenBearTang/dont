package com.ssafy.edu.awesomeproject.domain.fin.secretary.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request.StrictSecretaryEvaluateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response.StrictSecretaryResponse;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class StrictSecretaryServiceTest {

    @Mock private AiClient aiClient;

    @Mock private UserRepository userRepository;

    @Mock private CardTransactionRepository cardTransactionRepository;

    private StrictSecretaryService strictSecretaryService;

    @BeforeEach
    void setUp() {
        strictSecretaryService =
                new StrictSecretaryService(aiClient, userRepository, cardTransactionRepository);
    }

    @Test
    void evaluatePurchaseDelegatesToAiWithSpringComposedContext() {
        User user = org.mockito.Mockito.mock(User.class);
        when(user.getName()).thenReturn("테스트유저");
        when(user.getMonthlySavingGoalAmount()).thenReturn(new BigDecimal("1200000"));
        when(userRepository.findActiveById(10L)).thenReturn(Optional.of(user));

        CardTransaction transaction =
                CardTransaction.builder()
                        .card(null)
                        .transactionDate(LocalDate.now())
                        .transactionTime("12:34:56")
                        .merchantName("테스트몰")
                        .categoryName("전자제품")
                        .transactionAmount(300000L)
                        .transactionType("PAYMENT")
                        .approvalNo("A1")
                        .description("결제")
                        .userId(10L)
                        .build();
        when(cardTransactionRepository
                        .findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                org.mockito.ArgumentMatchers.eq(10L),
                                org.mockito.ArgumentMatchers.any(),
                                org.mockito.ArgumentMatchers.any()))
                .thenReturn(List.of(transaction));

        StrictSecretaryResponse expected =
                StrictSecretaryResponse.builder()
                        .is_approved(true)
                        .fact_violence_comment("가능")
                        .reasoning(List.of("근거"))
                        .build();
        when(aiClient.evaluatePurchase(any())).thenReturn(expected);

        StrictSecretaryResponse result =
                strictSecretaryService.evaluatePurchase(10L, "노트북", "http://example.com", "업무용");

        assertThat(result).isSameAs(expected);
        ArgumentCaptor<StrictSecretaryEvaluateRequest> captor =
                ArgumentCaptor.forClass(StrictSecretaryEvaluateRequest.class);
        verify(aiClient).evaluatePurchase(captor.capture());
        verify(aiClient, never()).evaluatePurchaseFromDb(any());

        StrictSecretaryEvaluateRequest payload = captor.getValue();
        assertThat(payload.userProfile().userId()).isEqualTo("10");
        assertThat(payload.userProfile().name()).isEqualTo("테스트유저");
        assertThat(payload.userProfile().monthlyIncome()).isEqualTo(1_200_000);
        assertThat(payload.recentTransactions()).hasSize(1);
        assertThat(payload.recentTransactions().get(0).transactionTime()).isEqualTo("123456");
    }

    @Test
    void evaluatePurchaseReturnsFallbackWhenAiFails() {
        User user = org.mockito.Mockito.mock(User.class);
        when(user.getName()).thenReturn("테스트유저");
        when(user.getMonthlySavingGoalAmount()).thenReturn(new BigDecimal("0"));
        when(userRepository.findActiveById(10L)).thenReturn(Optional.of(user));
        when(cardTransactionRepository
                        .findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                org.mockito.ArgumentMatchers.eq(10L),
                                org.mockito.ArgumentMatchers.any(),
                                org.mockito.ArgumentMatchers.any()))
                .thenReturn(List.of());
        when(aiClient.evaluatePurchase(any())).thenThrow(new RuntimeException("down"));

        StrictSecretaryResponse result =
                strictSecretaryService.evaluatePurchase(10L, "모니터", "http://example.com", "필요");

        assertThat(result.is_approved()).isFalse();
        assertThat(result.getFact_violence_comment()).contains("오류");
        assertThat(result.getReasoning()).isNotEmpty();
    }
}
