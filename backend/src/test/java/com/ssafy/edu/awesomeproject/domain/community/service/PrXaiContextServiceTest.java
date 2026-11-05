package com.ssafy.edu.awesomeproject.domain.community.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiEvaluationRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrStatus;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrPostRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.profile.dto.response.FinanceProfileResponse;
import com.ssafy.edu.awesomeproject.domain.fin.profile.service.FinanceBudgetBasisService;
import com.ssafy.edu.awesomeproject.domain.fin.profile.service.FinanceProfileService;
import com.ssafy.edu.awesomeproject.domain.fin.profile.service.MonthlyBudgetBasisEstimator;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class PrXaiContextServiceTest {

    @Mock private PrPostRepository prPostRepository;
    @Mock private UserRepository userRepository;
    @Mock private FinanceProfileService financeProfileService;
    @Mock private FinanceBudgetBasisService financeBudgetBasisService;
    @Mock private CardTransactionRepository cardTransactionRepository;
    @Mock private AccountRepository accountRepository;
    @Mock private SavingsSettingRepository savingsSettingRepository;

    private PrXaiContextService prXaiContextService;

    @BeforeEach
    void setUp() {
        prXaiContextService =
                new PrXaiContextService(
                        prPostRepository,
                        userRepository,
                        financeProfileService,
                        financeBudgetBasisService,
                        cardTransactionRepository,
                        accountRepository,
                        savingsSettingRepository);
    }

    @Test
    void buildContextAssemblesPurchaseFinanceAndTransactions() {
        User viewer = org.mockito.Mockito.mock(User.class);
        User author = org.mockito.Mockito.mock(User.class);
        when(author.getId()).thenReturn(21L);
        when(userRepository.findActiveById(10L)).thenReturn(Optional.of(viewer));

        Board board = org.mockito.Mockito.mock(Board.class);
        PostStub post = new PostStub(67L, author, board, "맥북 PR", "개발용 장비가 필요합니다.");
        PrPost prPost = new PrPost(post, "맥북 프로", 2500000L, "IT", "https://example.com/mac", LocalDateTime.now().plusDays(2));
        setPrPostId(prPost, 67L);
        when(prPostRepository.findByPost_Id(67L)).thenReturn(Optional.of(prPost));

        when(financeProfileService.getFinanceProfile(anyString()))
                .thenReturn(new FinanceProfileResponse(3000000.0, 800000.0, 250000.0, 12));

        CardTransaction transaction =
                CardTransaction.builder()
                        .card(null)
                        .transactionDate(LocalDate.of(2026, 3, 20))
                        .transactionTime("12:34:56")
                        .merchantName("테스트몰")
                        .categoryName("전자제품")
                        .transactionAmount(120000L)
                        .userId(10L)
                        .build();
        when(cardTransactionRepository
                        .findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                org.mockito.ArgumentMatchers.eq(21L),
                                org.mockito.ArgumentMatchers.any(),
                                org.mockito.ArgumentMatchers.any()))
                .thenReturn(List.of(transaction));

        PrXaiEvaluationRequestDto result = prXaiContextService.buildContext(67L, 10L);

        assertThat(result.requestId()).isNotBlank();
        assertThat(result.purchase().postId()).isEqualTo(67L);
        assertThat(result.purchase().itemName()).isEqualTo("맥북 프로");
        assertThat(result.financeProfile().currentBalance().source()).isEqualTo("spring.finance_profile");
        assertThat(result.financeProfile().currentBalance().snapshotId()).contains("21");
        assertThat(result.recentTransactions()).hasSize(1);
        assertThat(result.recentTransactions().get(0).transactionTime()).isEqualTo("123456");
    }

    private PrXaiEvaluationRequestDto buildContextWithBudgetBasis(
            Optional<MonthlyBudgetBasisEstimator.Basis> basis) {
        User viewer = org.mockito.Mockito.mock(User.class);
        User author = org.mockito.Mockito.mock(User.class);
        when(author.getId()).thenReturn(21L);
        when(userRepository.findActiveById(10L)).thenReturn(Optional.of(viewer));
        Board board = org.mockito.Mockito.mock(Board.class);
        PostStub post = new PostStub(67L, author, board, "MX Master 3S 살까요?", "마우스가 필요합니다.");
        PrPost prPost = new PrPost(post, "MX Master 3S", 130000L, "전자기기", "https://example.com/mx", LocalDateTime.now().plusDays(2));
        setPrPostId(prPost, 67L);
        when(prPostRepository.findByPost_Id(67L)).thenReturn(Optional.of(prPost));
        when(financeProfileService.getFinanceProfile(anyString()))
                .thenReturn(new FinanceProfileResponse(1500000.0, 300000.0, 200000.0, 9));
        when(financeBudgetBasisService.estimate(21L)).thenReturn(basis);
        return prXaiContextService.buildContext(67L, 10L);
    }

    @Test
    void buildContextSendsEstimatedIncomeAndFixedExpenseWithTheirProvenance() {
        PrXaiEvaluationRequestDto result =
                buildContextWithBudgetBasis(
                        Optional.of(new MonthlyBudgetBasisEstimator.Basis(2_600_000L, 600_000L, 3)));

        // 5·3·2 예산 규칙이 꺼져 있던 원인: 이 두 값을 보내지 않았다.
        assertThat(result.financeProfile().availableFixedIncome().value()).isEqualTo(2_600_000L);
        assertThat(result.financeProfile().availableFixedExpense().value()).isEqualTo(600_000L);
        for (var value :
                List.of(
                        result.financeProfile().availableFixedIncome(),
                        result.financeProfile().availableFixedExpense())) {
            assertThat(value.isEstimated()).isTrue(); // 추정값은 추정이라고 밝힌다
            assertThat(value.isDefault()).isFalse();
            assertThat(value.estimationMethod()).isEqualTo(MonthlyBudgetBasisEstimator.METHOD);
            assertThat(value.source()).isEqualTo("spring.account_transactions");
        }
        assertThat(result.financeProfile().availableFixedIncome().snapshotId()).contains("income").contains("21");
        assertThat(result.financeProfile().availableFixedExpense().snapshotId()).contains("fixed-expense").contains("21");
    }

    @Test
    void buildContextOmitsIncomeAndFixedExpenseWhenThereIsNothingToEstimateFrom() throws Exception {
        PrXaiEvaluationRequestDto result = buildContextWithBudgetBasis(Optional.empty());

        // 근거가 없으면 보내지 않는다. 기본값(0원, 100만 원)으로 채우면 AI 가 판단 불가가 아니라 틀린 값을 믿는다.
        assertThat(result.financeProfile().availableFixedIncome()).isNull();
        assertThat(result.financeProfile().availableFixedExpense()).isNull();
        String json = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(result.financeProfile());
        assertThat(json).doesNotContain("availableFixed");
        assertThat(json).contains("currentBalance");
    }

    @Test
    void buildContextThrowsWhenPrMissing() {
        User user = org.mockito.Mockito.mock(User.class);
        when(userRepository.findActiveById(10L)).thenReturn(Optional.of(user));
        when(prPostRepository.findByPost_Id(67L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> prXaiContextService.buildContext(67L, 10L))
                .isInstanceOf(CommunityException.class);
    }

    private static final class PostStub extends com.ssafy.edu.awesomeproject.domain.community.entity.Post {
        PostStub(Long id, User user, Board board, String title, String content) {
            super(board, user, title, content);
            try {
                java.lang.reflect.Field idField = com.ssafy.edu.awesomeproject.domain.community.entity.Post.class.getDeclaredField("id");
                idField.setAccessible(true);
                idField.set(this, id);
            } catch (ReflectiveOperationException exception) {
                throw new IllegalStateException(exception);
            }
        }
    }

    private static void setPrPostId(PrPost prPost, Long postId) {
        try {
            java.lang.reflect.Field idField = PrPost.class.getDeclaredField("postId");
            idField.setAccessible(true);
            idField.set(prPost, postId);
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException(exception);
        }
    }
}
