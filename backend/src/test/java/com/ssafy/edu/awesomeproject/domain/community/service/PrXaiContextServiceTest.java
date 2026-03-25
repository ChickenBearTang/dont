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
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.profile.dto.response.FinanceProfileResponse;
import com.ssafy.edu.awesomeproject.domain.fin.profile.service.FinanceProfileService;
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
    @Mock private CardTransactionRepository cardTransactionRepository;

    private PrXaiContextService prXaiContextService;

    @BeforeEach
    void setUp() {
        prXaiContextService =
                new PrXaiContextService(
                        prPostRepository,
                        userRepository,
                        financeProfileService,
                        cardTransactionRepository);
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
