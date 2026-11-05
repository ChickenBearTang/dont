package com.ssafy.edu.awesomeproject.domain.fin.card.service;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.AiCardRecommendationDbRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.CardRegisterRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.MockCardTransactionRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.AiDateRangeRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.AiAnalysisResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardRecommendationResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardSummaryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.Card;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Collections;
import java.util.Comparator;
import java.util.Locale;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.time.Duration;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Slf4j
@RequiredArgsConstructor
public class CardService {

    private static final String SUCCESS_CODE = "H0000";
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.BASIC_ISO_DATE;
    private static final DateTimeFormatter ISO_DATE_FORMATTER = DateTimeFormatter.ISO_LOCAL_DATE;
    private static final int RECOMMENDATION_CACHE_MAXIMUM_SIZE = 2_000;
    private static final Duration RECOMMENDATION_CACHE_TTL = Duration.ofMinutes(5);

    private final CardRepository cardRepository;
    private final CardTransactionRepository cardTransactionRepository;
    private final UserRepository userRepository;
    private final AccountRepository accountRepository;
    private final AiClient aiClient;
    private final MonthlyTransactionFingerprintService monthlyTransactionFingerprintService;
    private final Cache<String, CardRecommendationResponse> recommendationCache =
            Caffeine.newBuilder()
                    .maximumSize(RECOMMENDATION_CACHE_MAXIMUM_SIZE)
                    .expireAfterWrite(RECOMMENDATION_CACHE_TTL)
                    .build();

    @Value("${finance.mock-data.enabled:false}")
    private boolean mockDataEnabled;

    @Transactional(readOnly = true)
    public CardListResponse getCardList(Long userId) {
        List<Card> cards = cardRepository.findAllByUser_Id(userId);
        return buildCardListResponse(userId, cards, true, "Card list retrieved.");
    }

    @Transactional(readOnly = true)
    public CardListResponse.CardItem getCardItem(Long userId, Long cardId, String startDate, String endDate) {
        Card card =
                cardRepository
                        .findByIdAndUserId(cardId, userId)
                        .orElseThrow(
                                () ->
                                        new IllegalArgumentException(
                                                "Card not found for userId="
                                                        + userId
                                                        + ", cardId="
                                                        + cardId));

        LocalDate start = parseDateOrThrow(startDate, "startDate");
        LocalDate end = parseDateOrThrow(endDate, "endDate");
        if (start.isAfter(end)) {
            throw new IllegalArgumentException("startDate must be before or equal to endDate.");
        }

        List<CardTransaction> transactions =
                cardTransactionRepository
                        .findByCardIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                cardId, start, end);

        Long totalAmount = transactions.stream().mapToLong(CardTransaction::getTransactionAmount).sum();

        return CardListResponse.CardItem.builder()
                .cardIssuerName(card.getCardIssuerName())
                .cardName(card.getCardName())
                .monthlyCardExpense(totalAmount)
                .build();
    }

    @Transactional(readOnly = true)
    public CardTransactionResponse getCardTransactions(
            Long userId, Long cardId, String startDate, String endDate) {
        Card card =
                cardRepository
                        .findByIdAndUserId(cardId, userId)
                        .orElseThrow(
                                () ->
                                        new IllegalArgumentException(
                                                "Card not found for userId="
                                                        + userId
                                                        + ", cardId="
                                                        + cardId));

        LocalDate start = parseDateOrThrow(startDate, "startDate");
        LocalDate end = parseDateOrThrow(endDate, "endDate");
        if (start.isAfter(end)) {
            throw new IllegalArgumentException("startDate must be before or equal to endDate.");
        }

        List<CardTransaction> transactions =
                cardTransactionRepository
                        .findByCardIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                cardId, start, end);

        return buildCardTransactionListResponse(
                transactions, true, "Card transactions retrieved.", card.getCardNo(), card.getCardName());
    }

    @Transactional(readOnly = true)
    public CardSummaryResponse getCardSummary(Long userId, String startDate, String endDate) {
        return getCardSummary(userId, startDate, endDate, true);
    }

    @Transactional(readOnly = true)
    public CardSummaryResponse getCardSummary(
            Long userId, String startDate, String endDate, boolean includeAi) {
        LocalDate start = parseDateOrThrow(startDate, "startDate");
        LocalDate end = parseDateOrThrow(endDate, "endDate");
        if (start.isAfter(end)) {
            throw new IllegalArgumentException("startDate must be before or equal to endDate.");
        }

        List<CardTransaction> transactions =
                cardTransactionRepository
                        .findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                userId, start, end);

        Long totalAmount =
                transactions.stream().mapToLong(this::safeTransactionAmount).sum();

        Map<String, Long> amountByCategory =
                transactions.stream()
                        .collect(
                                Collectors.groupingBy(
                                        this::normalizeCategoryName,
                                        Collectors.summingLong(this::safeTransactionAmount)));

        List<CardSummaryResponse.RankColum> rankColumList =
                amountByCategory.entrySet().stream()
                        .map(
                                entry -> {
                                    long amount = entry.getValue();
                                    double percentage =
                                            totalAmount == 0 ? 0.0 : (amount * 100.0) / totalAmount;

                                    return CardSummaryResponse.RankColum.builder()
                                            .categoryName(entry.getKey())
                                            .percentage(percentage)
                                            .amount((int) amount)
                                            .build();
                                })
                        .sorted(Comparator.comparing(CardSummaryResponse.RankColum::getPercentage).reversed())
                        .toList();

        return CardSummaryResponse.builder()
                .success(true)
                .code(SUCCESS_CODE)
                .message("Card summary retrieved.")
                .totalAmount(totalAmount)
                .RankColumList(rankColumList)
                .aiReport(includeAi ? getAiAnalysis(userId, start, end) : null)
                .build();
    }

    private long safeTransactionAmount(CardTransaction transaction) {
        return transaction.getTransactionAmount() == null ? 0L : transaction.getTransactionAmount();
    }

    private String normalizeCategoryName(CardTransaction transaction) {
        String categoryName = transaction.getCategoryName();
        if (categoryName == null || categoryName.isBlank()) {
            return "기타";
        }
        return categoryName;
    }

    private AiAnalysisResponse getAiAnalysis(Long userId, LocalDate start, LocalDate end) {
        try {
            AiAnalysisResponse response =
                    aiClient.analyzeConsumptionByDateRange(
                            new AiDateRangeRequest(
                                    userId, start.format(DATE_FORMATTER), end.format(DATE_FORMATTER)));
            if (response == null) {
                System.err.println("AI Analysis returned null response");
                return null;
            }
            return response;
        } catch (Exception e) {
            System.err.println("AI Analysis failed: " + e.getMessage());
            return null;
        }
    }

    private CardTransactionResponse buildCardTransactionListResponse(
            List<CardTransaction> cardTransactions,
            boolean success,
            String message,
            String cardNo,
            String cardName) {
        String code = success ? "TRANSACTION_200_1" : "TRANSACTION_500_1";
        return CardTransactionResponse.builder()
                .success(success)
                .code(code)
                .message(message)
                .cardName(cardName)
                .cardNo(cardNo)
                .transaction(
                        cardTransactions == null
                                ? Collections.emptyList()
                                : cardTransactions.stream()
                                        .map(
                                                cardTransaction ->
                                                        CardTransactionResponse.TransactionItem.builder()
                                                                .categoryName(cardTransaction.getCategoryName())
                                                                .merchantName(cardTransaction.getMerchantName())
                                                                .transactionDate(
                                                                        cardTransaction.getTransactionDate() == null
                                                                                ? null
                                                                                : cardTransaction
                                                                                        .getTransactionDate()
                                                                                        .format(DATE_FORMATTER))
                                                                .transactionTime(cardTransaction.getTransactionTime())
                                                                .transactionAmount(
                                                                        cardTransaction.getTransactionAmount() == null
                                                                                ? null
                                                                                : String.valueOf(
                                                                                        cardTransaction
                                                                                                .getTransactionAmount()))
                                                                .id(cardTransaction.getId())
                                                                .build())
                                        .collect(Collectors.toList()))
                .build();
    }

    private CardListResponse buildCardListResponse(
            Long userId, List<Card> cards, boolean success, String message) {
        String code = success ? "TRANSACTION_200_1" : "TRANSACTION_500_1";
        Map<Long, Long> monthlyExpenseByCardId = getCurrentMonthExpenseByCardId(userId, cards);
        return CardListResponse.builder()
                .success(success)
                .code(code)
                .message(message)
                .cards(
                        cards == null
                                ? Collections.emptyList()
                                : cards.stream()
                                        .sorted(
                                                Comparator.comparingLong(
                                                                (Card card) ->
                                                                        monthlyExpenseByCardId.getOrDefault(
                                                                                card.getId(), 0L))
                                                        .reversed())
                                        .map(
                                                card ->
                                                        CardListResponse.CardItem.builder()
                                                                .id(card.getId())
                                                                .cardIssuerName(card.getCardIssuerName())
                                                                .cardName(card.getCardName())
                                                                .monthlyCardExpense(
                                                                        monthlyExpenseByCardId.getOrDefault(
                                                                                card.getId(), 0L))
                                                                .build())
                                        .collect(Collectors.toList()))
                .build();
    }

    private Map<Long, Long> getCurrentMonthExpenseByCardId(Long userId, List<Card> cards) {
        if (userId == null || cards == null || cards.isEmpty()) {
            return Collections.emptyMap();
        }

        LocalDate today = LocalDate.now();
        LocalDate firstDayOfMonth = today.withDayOfMonth(1);

        return cardTransactionRepository.findMonthlyExpenseByUserIdAndDateRange(userId, firstDayOfMonth, today)
                .stream()
                .collect(
                        Collectors.toMap(
                                CardTransactionRepository.CardMonthlyExpenseProjection::getCardId,
                                projection ->
                                        projection.getTotalAmount() == null ? 0L : projection.getTotalAmount()));
    }

    // ------------------------------------------------------------------ 개발·시연용 입력

    /**
     * 카드를 등록한다. 외부 카드사 연동이 없어서 카드가 생기는 경로가 이것과 데모 DB 뿐이다. 설정으로 켠 환경에서만
     * 동작한다 (finance.mock-data.enabled=true).
     */
    @Transactional
    public CardListResponse.CardItem registerCard(Long userId, CardRegisterRequest request) {
        requireMockData();
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
        String withdrawalAccountNo =
                accountRepository.findAllByUserId(userId).stream()
                        .filter(account -> account.getAccountRole() == AccountRole.LINKED_DEPOSIT)
                        .min(
                                Comparator.comparing((Account account) -> !account.isPrimary())
                                        .thenComparing(Account::getId))
                        .map(Account::getAccountNo)
                        .orElse(null);
        Card card =
                cardRepository.save(
                        Card.builder()
                                .user(user)
                                .cardNo(randomDigits("9", 15))
                                .cvc("000") // 실제 카드가 아니라서 쓰지 않는다 (열이 NOT NULL 이라 채운다)
                                .cardUniqueNo("LOCAL-" + UUID.randomUUID())
                                .cardIssuerCode("999")
                                .cardIssuerName(request.cardIssuerName().strip())
                                .cardName(request.cardName().strip())
                                .cardDescription("개발·시연용 카드")
                                .cardExpiryDate(LocalDate.now().plusYears(5).format(DATE_FORMATTER))
                                .withdrawalAccountNo(withdrawalAccountNo)
                                .withdrawalDate(
                                        request.withdrawalDate() == null || request.withdrawalDate().isBlank()
                                                ? "1"
                                                : request.withdrawalDate())
                                .build());
        return CardListResponse.CardItem.builder()
                .id(card.getId())
                .cardIssuerName(card.getCardIssuerName())
                .cardName(card.getCardName())
                .monthlyCardExpense(0L)
                .build();
    }

    /** 카드 결제내역 한 건을 입력한다 (개발·시연용). */
    @Transactional
    public CardTransactionResponse.TransactionItem addMockTransaction(
            Long userId, Long cardId, MockCardTransactionRequest request) {
        requireMockData();
        Card card =
                cardRepository
                        .findByIdAndUserId(cardId, userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));
        LocalDate date =
                request.transactionDate() == null || request.transactionDate().isBlank()
                        ? LocalDate.now()
                        : parseDateOrThrow(request.transactionDate().strip(), "transactionDate");
        CardTransaction saved =
                cardTransactionRepository.save(
                        CardTransaction.builder()
                                .card(card)
                                .userId(userId)
                                .transactionDate(date)
                                .transactionTime(LocalTime.now().format(DateTimeFormatter.ofPattern("HHmmss")))
                                .merchantName(request.merchantName().strip())
                                .categoryName(
                                        request.categoryName() == null || request.categoryName().isBlank()
                                                ? null
                                                : request.categoryName().strip())
                                .transactionAmount(request.amount())
                                .transactionType("PAYMENT")
                                .approvalNo(randomDigits("APP", 8))
                                .description("mock")
                                .build());
        return CardTransactionResponse.TransactionItem.builder()
                .id(saved.getId())
                .merchantName(saved.getMerchantName())
                .categoryName(saved.getCategoryName())
                .transactionDate(saved.getTransactionDate().format(DATE_FORMATTER))
                .transactionTime(saved.getTransactionTime())
                .transactionAmount(String.valueOf(saved.getTransactionAmount()))
                .build();
    }

    private void requireMockData() {
        if (!mockDataEnabled) {
            throw new AccountException(AccountErrorCode.MOCK_DATA_DISABLED);
        }
    }

    private static String randomDigits(String prefix, int count) {
        StringBuilder digits = new StringBuilder(prefix);
        for (int i = 0; i < count; i++) {
            digits.append(ThreadLocalRandom.current().nextInt(10));
        }
        return digits.toString();
    }

    private LocalDate parseDateOrThrow(String date, String fieldName) {
        try {
            return LocalDate.parse(date, DATE_FORMATTER);
        } catch (DateTimeParseException exception) {
            try {
                return LocalDate.parse(date, ISO_DATE_FORMATTER);
            } catch (DateTimeParseException ignored) {
                throw new IllegalArgumentException(fieldName + " must be yyyyMMdd or yyyy-MM-dd format.");
            }
        }
    }

    @Transactional(readOnly = true)
    public CardRecommendationResponse getCardRecommendation(Long userId, String monthStr) {
        try {
            YearMonth yearMonth = YearMonth.parse(monthStr);
            String transactionFingerprint =
                    monthlyTransactionFingerprintService.buildMonthlyFingerprint(userId, yearMonth);
            String cacheKey = recommendationCacheKey(userId, monthStr, transactionFingerprint);
            CardRecommendationResponse cached = recommendationCache.getIfPresent(cacheKey);
            if (cached != null) {
                return cached;
            }

            CardRecommendationResponse response =
                    aiClient.getCardRecommendationFromDb(
                    new AiCardRecommendationDbRequest(userId, monthStr));
            if (response == null) {
                log.warn(
                        "Card recommendation returned null from AI. userId={}, month={}",
                        userId,
                        monthStr);
            } else {
                recommendationCache.put(cacheKey, response);
            }
            return response;
        } catch (Exception e) {
            log.warn(
                    "AI Card Recommendation failed. userId={}, month={}",
                    userId,
                    monthStr,
                    e);
            return null;
        }
    }

    private String recommendationCacheKey(Long userId, String monthStr, String transactionFingerprint) {
        return userId
                + ":"
                + monthStr
                + ":"
                + transactionFingerprint.toLowerCase(Locale.ROOT);
    }

}
