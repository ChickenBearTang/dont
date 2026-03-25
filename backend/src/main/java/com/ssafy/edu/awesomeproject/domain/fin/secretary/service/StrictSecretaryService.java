package com.ssafy.edu.awesomeproject.domain.fin.secretary.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request.StrictSecretaryEvaluateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response.StrictSecretaryResponse;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class StrictSecretaryService {

    private static final DateTimeFormatter BASIC_DATE = DateTimeFormatter.BASIC_ISO_DATE;

    private final AiClient aiClient;
    private final UserRepository userRepository;
    private final CardTransactionRepository cardTransactionRepository;

    public StrictSecretaryResponse evaluatePurchase(
            Long userId, String itemText, String itemLink, String userReason) {
        if (userId == null) {
            return fallback("로그인 사용자 정보를 확인하지 못했습니다.");
        }

        try {
            User user =
                    userRepository
                            .findActiveById(userId)
                            .orElseThrow(
                                    () ->
                                            new IllegalArgumentException(
                                                    "Active user not found: " + userId));
            List<StrictSecretaryEvaluateRequest.RecentTransaction> recentTransactions =
                    fetchRecentTransactions(userId);

            StrictSecretaryEvaluateRequest request =
                    new StrictSecretaryEvaluateRequest(
                            new StrictSecretaryEvaluateRequest.UserProfile(
                                    String.valueOf(userId),
                                    user.getName(),
                                    resolveMonthlyIncome(user, recentTransactions)),
                            safeText(itemText),
                            safeText(itemLink),
                            safeText(userReason),
                            recentTransactions,
                            null);
            StrictSecretaryResponse response = aiClient.evaluatePurchase(request);
            if (response == null) {
                throw new IllegalStateException("AI strict-secretary response is empty");
            }
            return response;
        } catch (Exception exception) {
            log.warn("strict-secretary evaluate failed: {}", exception.getMessage());
            return fallback("AI 판단 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
        }
    }

    private List<StrictSecretaryEvaluateRequest.RecentTransaction> fetchRecentTransactions(Long userId) {
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusMonths(3);

        return cardTransactionRepository
                .findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                        userId, startDate, endDate)
                .stream()
                .limit(50)
                .map(this::toRecentTransaction)
                .toList();
    }

    private StrictSecretaryEvaluateRequest.RecentTransaction toRecentTransaction(
            CardTransaction tx) {
        String transactionDate =
                tx.getTransactionDate() == null ? "" : tx.getTransactionDate().format(BASIC_DATE);
        String transactionTime =
                tx.getTransactionTime() == null
                        ? "000000"
                        : tx.getTransactionTime().replaceAll("[^0-9]", "");
        String normalizedTime =
                transactionTime.isBlank() ? "000000" : transactionTime.substring(0, Math.min(6, transactionTime.length()));

        long rawAmount = tx.getTransactionAmount() == null ? 0L : tx.getTransactionAmount();
        int boundedAmount =
                rawAmount > Integer.MAX_VALUE
                        ? Integer.MAX_VALUE
                        : (rawAmount < Integer.MIN_VALUE ? Integer.MIN_VALUE : (int) rawAmount);

        return new StrictSecretaryEvaluateRequest.RecentTransaction(
                transactionDate,
                normalizedTime,
                safeText(tx.getMerchantName()),
                safeText(tx.getCategoryName()),
                boundedAmount,
                tx.getTransactionType(),
                tx.getApprovalNo(),
                tx.getDescription());
    }

    private int resolveMonthlyIncome(
            User user, List<StrictSecretaryEvaluateRequest.RecentTransaction> transactions) {
        BigDecimal monthlySavingGoal = user.getMonthlySavingGoalAmount();
        if (monthlySavingGoal != null && monthlySavingGoal.intValue() > 0) {
            return monthlySavingGoal.intValue();
        }

        if (transactions.isEmpty()) {
            return 0;
        }

        long total = transactions.stream().mapToLong(StrictSecretaryEvaluateRequest.RecentTransaction::transactionAmount).sum();
        long estimated = Math.max(0L, total / 3L);
        return estimated > Integer.MAX_VALUE ? Integer.MAX_VALUE : (int) estimated;
    }

    private StrictSecretaryResponse fallback(String message) {
        return StrictSecretaryResponse.builder()
                .is_approved(false)
                .fact_violence_comment(message)
                .reasoning(List.of("Spring-AI 위임 경로에서 오류가 발생했습니다."))
                .build();
    }

    private String safeText(String value) {
        return value == null ? "" : value;
    }
}
