package com.ssafy.edu.awesomeproject.domain.fin.card.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardSummaryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.Card;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankClient;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class CardService {

    private static final String SUCCESS_CODE = "H0000";
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.BASIC_ISO_DATE;
    private static final DateTimeFormatter ISO_DATE_FORMATTER = DateTimeFormatter.ISO_LOCAL_DATE;

    private final OpenBankClient openBankClient;
    private final CardRepository cardRepository;
    private final CardTransactionRepository cardTransactionRepository;
    private final UserRepository userRepository;

    @Value("${ssafy.api.key}")
    private String apiKey;

    @Transactional
    public CardListResponse getCardList(Long userId) {
        List<Card> cards = cardRepository.findAllByUser_Id(userId);
        if (cards.isEmpty()) {
            RefreshResult refreshResult = refreshCardsFromExternal(userId);
            return buildCardListResponse(
                    userId,
                    refreshResult.cards(),
                    refreshResult.success(),
                    refreshResult.success()
                            ? "Card list refreshed and retrieved."
                            : refreshResult.message());
        }
        return buildCardListResponse(userId, cards, true, "Card list retrieved.");
    }

    @Transactional
    public CardListResponse.CardItem getCardItem(
            Long userId, Long cardId, String startDate, String endDate) {

        Card card = cardRepository.findById(cardId).orElseThrow();

        LocalDate start = parseDateOrThrow(startDate, "startDate");
        LocalDate end = parseDateOrThrow(endDate, "endDate");
        if (start.isAfter(end)) {
            throw new IllegalArgumentException("startDate must be before or equal to endDate.");
        }

        List<CardTransaction> transactions =
                cardTransactionRepository
                        .findByCardIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                cardId, start, end);

        Long totalAmount =
                transactions.stream().mapToLong(CardTransaction::getTransactionAmount).sum();

        return CardListResponse.CardItem.builder()
                .cardIssuerName(card.getCardIssuerName())
                .cardName(card.getCardName())
                .monthlyCardExpense(totalAmount)
                .build();
    }

    @Transactional
    public CardListResponse refreshCardList(Long userId) {
        RefreshResult refreshResult = refreshCardsFromExternal(userId);
        return buildCardListResponse(
                userId, refreshResult.cards(), refreshResult.success(), refreshResult.message());
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
                transactions,
                true,
                "Card transactions retrieved.",
                card.getCardNo(),
                card.getCardName());
    }

    @Transactional(readOnly = true)
    public CardSummaryResponse getCardSummary(Long userId, String startDate, String endDate) {
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
                transactions.stream().mapToLong(CardTransaction::getTransactionAmount).sum();

        Map<String, Long> amountByCategory =
                transactions.stream()
                        .collect(
                                Collectors.groupingBy(
                                        CardTransaction::getCategoryName,
                                        Collectors.summingLong(
                                                CardTransaction::getTransactionAmount)));

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
                        .sorted(
                                Comparator.comparing(CardSummaryResponse.RankColum::getPercentage)
                                        .reversed())
                        .toList();

        return CardSummaryResponse.builder()
                .success(true)
                .code(SUCCESS_CODE)
                .message("Card summary retrieved.")
                .totalAmount(totalAmount)
                .RankColumList(rankColumList)
                .build();
    }

    private RefreshResult refreshCardsFromExternal(Long userId) {
        User user = getRequiredUserWithFinanceKey(userId);
        OpenBankRequest request = createCardListRequest(user.getSsafyFinanceUserKey());
        OpenBankResponse response = openBankClient.fetchCreditCardList(request);

        boolean success =
                response != null
                        && response.getHeader() != null
                        && SUCCESS_CODE.equals(response.getHeader().getResponseCode());

        if (!success || response.getRec() == null) {
            List<Card> currentCards = cardRepository.findAllByUser_Id(userId);
            return new RefreshResult(false, currentCards, "Failed to refresh card list.");
        }

        List<Card> existingCards = cardRepository.findAllByUser_Id(userId);

        Map<String, Card> existingCardMap =
                existingCards.stream()
                        .collect(Collectors.toMap(Card::getCardUniqueNo, card -> card));

        List<Card> resultCards = new ArrayList<>();

        for (OpenBankResponse.Rec rec : response.getRec()) {
            Card existingCard = existingCardMap.get(rec.getCardUniqueNo());

            if (existingCard != null) {
                existingCard.updateFromExternal(
                        rec.getCardNo(),
                        rec.getCvc(),
                        rec.getCardIssuerCode(),
                        rec.getCardIssuerName(),
                        rec.getCardName(),
                        rec.getCardDescription(),
                        rec.getBaselinePerformance(),
                        rec.getMaxBenefitLimit(),
                        rec.getCardExpiryDate(),
                        rec.getWithdrawalAccountNo(),
                        rec.getWithdrawalDate());
                resultCards.add(existingCard);
            } else {
                Card newCard = toCardEntity(user, rec);
                resultCards.add(cardRepository.save(newCard));
            }
        }

        return new RefreshResult(true, resultCards, "Card list refreshed.");
    }

    private OpenBankRequest createCardListRequest(String userKey) {
        LocalDateTime now = LocalDateTime.now();

        return OpenBankRequest.builder()
                .header(
                        OpenBankReqHeader.builder()
                                .apiName("inquireSignUpCreditCardList")
                                .transmissionDate(
                                        now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                                .transmissionTime(now.format(DateTimeFormatter.ofPattern("HHmmss")))
                                .institutionCode("00100")
                                .fintechAppNo("001")
                                .apiServiceCode("inquireSignUpCreditCardList")
                                .institutionTransactionUniqueNo(generateUniqueNo(now))
                                .apiKey(apiKey)
                                .userKey(userKey)
                                .build())
                .build();
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
                                                        CardTransactionResponse.TransactionItem
                                                                .builder()
                                                                .categoryName(
                                                                        cardTransaction
                                                                                .getCategoryName())
                                                                .merchantName(
                                                                        cardTransaction
                                                                                .getMerchantName())
                                                                .transactionDate(
                                                                        cardTransaction
                                                                                                .getTransactionDate()
                                                                                        == null
                                                                                ? null
                                                                                : cardTransaction
                                                                                        .getTransactionDate()
                                                                                        .format(
                                                                                                DATE_FORMATTER))
                                                                .transactionTime(
                                                                        cardTransaction
                                                                                .getTransactionTime())
                                                                .transactionAmount(
                                                                        cardTransaction
                                                                                                .getTransactionAmount()
                                                                                        == null
                                                                                ? null
                                                                                : String.valueOf(
                                                                                        cardTransaction
                                                                                                .getTransactionAmount()))
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
                                                                        monthlyExpenseByCardId
                                                                                .getOrDefault(
                                                                                        card
                                                                                                .getId(),
                                                                                        0L))
                                                        .reversed())
                                        .map(
                                                card ->
                                                        CardListResponse.CardItem.builder()
                                                                .id(card.getId())
                                                                .cardIssuerName(
                                                                        card.getCardIssuerName())
                                                                .cardName(card.getCardName())
                                                                .monthlyCardExpense(
                                                                        monthlyExpenseByCardId
                                                                                .getOrDefault(
                                                                                        card
                                                                                                .getId(),
                                                                                        0L))
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

        return cardTransactionRepository
                .findMonthlyExpenseByUserIdAndDateRange(userId, firstDayOfMonth, today)
                .stream()
                .collect(
                        Collectors.toMap(
                                CardTransactionRepository.CardMonthlyExpenseProjection::getCardId,
                                projection ->
                                        projection.getTotalAmount() == null
                                                ? 0L
                                                : projection.getTotalAmount()));
    }

    private Card toCardEntity(User user, OpenBankResponse.Rec rec) {
        return Card.builder()
                .user(user)
                .cardNo(rec.getCardNo())
                .cvc(rec.getCvc())
                .cardUniqueNo(rec.getCardUniqueNo())
                .cardIssuerCode(rec.getCardIssuerCode())
                .cardIssuerName(rec.getCardIssuerName())
                .cardName(rec.getCardName())
                .cardDescription(rec.getCardDescription())
                .baselinePerformance(rec.getBaselinePerformance())
                .maxBenefitLimit(rec.getMaxBenefitLimit())
                .cardExpiryDate(rec.getCardExpiryDate())
                .withdrawalAccountNo(rec.getWithdrawalAccountNo())
                .withdrawalDate(rec.getWithdrawalDate())
                .build();
    }

    private User getRequiredUserWithFinanceKey(Long userId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () -> new IllegalArgumentException("User not found: " + userId));

        String financeUserKey = user.getSsafyFinanceUserKey();
        if (financeUserKey == null || financeUserKey.isBlank()) {
            throw new IllegalArgumentException(
                    "ssafy_finance_user_key is missing for userId=" + userId);
        }

        return user;
    }

    private LocalDate parseDateOrThrow(String date, String fieldName) {
        try {
            return LocalDate.parse(date, DATE_FORMATTER);
        } catch (DateTimeParseException exception) {
            try {
                return LocalDate.parse(date, ISO_DATE_FORMATTER);
            } catch (DateTimeParseException ignored) {
                throw new IllegalArgumentException(
                        fieldName + " must be yyyyMMdd or yyyy-MM-dd format.");
            }
        }
    }

    private String generateUniqueNo(LocalDateTime now) {
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        int randomNo = new Random().nextInt(900000) + 100000;
        return timestamp + randomNo;
    }

    private record RefreshResult(boolean success, List<Card> cards, String message) {}
}
