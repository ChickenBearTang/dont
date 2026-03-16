package com.ssafy.edu.awesomeproject.domain.fin.card.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request.OpenBankCardTransactionRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankCardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.Card;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankClient;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class CardService {

    private static final String SUCCESS_CODE = "H0000";

    private final OpenBankClient openBankClient;
    private final CardRepository cardRepository;
    private final UserRepository userRepository;

    @Value("${auth.api.key}")
    private String apiKey;

    // 키드 목록 불러오기
    @Transactional
    public CardListResponse getCardList(Long userId) {
        List<Card> cards = cardRepository.findAllByUserId(userId);

        if (cards.isEmpty()) {
            RefreshResult refreshResult = refreshCardsFromExternal(userId);
            return buildCardListResponse(
                refreshResult.cards(),
                refreshResult.success(),
                refreshResult.success() ? "Card list refreshed and retrieved." : refreshResult.message());
        }
        return buildCardListResponse(cards, true, "Card list retrieved.");
    }

    @Transactional
    public CardListResponse refreshCardList(Long userId) {


        RefreshResult refreshResult = refreshCardsFromExternal(userId);
        return buildCardListResponse(refreshResult.cards(), refreshResult.success(), refreshResult.message());
    }

    @Transactional
    public CardTransactionResponse getCardTransactions(
        Long userId, String cardNo, String startDate, String endDate) {
        User user = getRequiredUserWithFinanceKey(userId);
        CardCredential credential = resolveCardCredential(userId, cardNo);
        OpenBankCardTransactionRequest request =
            createCardTransactionRequest(
                user.getSsafyFinanceUserKey(),
                credential.cardNo(),
                credential.cvc(),
                startDate,
                endDate);
        OpenBankCardTransactionResponse response = openBankClient.fetchCreditCardTransactions(request);
        return convertToCardTransactionResponse(response, cardNo);
    }

    private RefreshResult refreshCardsFromExternal(Long userId) {
        User user = getRequiredUserWithFinanceKey(userId);
        OpenBankRequest request = createCardListRequest(user.getSsafyFinanceUserKey());
        OpenBankResponse response = openBankClient.fetchCreditCardList(request);

        boolean success = response != null
            && response.getHeader() != null
            && SUCCESS_CODE.equals(response.getHeader().getResponseCode());

        if (!success || response.getRec() == null) {
            List<Card> currentCards = cardRepository.findAllByUserId(userId);
            return new RefreshResult(false, currentCards, "Failed to refresh card list.");
        }

        cardRepository.deleteByUserId(userId);

        List<Card> savedCards = cardRepository.saveAll(
            response.getRec().stream()
                .map(rec -> toCardEntity(user, rec))
                .collect(Collectors.toList()));

        return new RefreshResult(true, savedCards, "Card list refreshed.");
    }

    private OpenBankRequest createCardListRequest(String userKey) {
        LocalDateTime now = LocalDateTime.now();

        return OpenBankRequest.builder()
            .header(OpenBankReqHeader.builder()
                .apiName("inquireSignUpCreditCardList")
                .transmissionDate(now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
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

    private OpenBankCardTransactionRequest createCardTransactionRequest(
        String userKey,
        String cardNo,
        String cvc,
        String startDate,
        String endDate) {
        LocalDateTime now = LocalDateTime.now();

        return OpenBankCardTransactionRequest.builder()
            .header(OpenBankReqHeader.builder()
                .apiName("inquireCreditCardTransactionList")
                .transmissionDate(now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                .transmissionTime(now.format(DateTimeFormatter.ofPattern("HHmmss")))
                .institutionCode("00100")
                .fintechAppNo("001")
                .apiServiceCode("inquireCreditCardTransactionList")
                .institutionTransactionUniqueNo(generateUniqueNo(now))
                .apiKey(apiKey)
                .userKey(userKey)
                .build())
            .cardNo(cardNo)
            .cvc(cvc)
            .startDate(startDate)
            .endDate(endDate)
            .build();
    }

    private CardListResponse buildCardListResponse(List<Card> cards, boolean success, String message) {
        String code = success ? "TRANSACTION_200_1" : "TRANSACTION_500_1";
        return CardListResponse.builder()
            .success(success)
            .code(code)
            .message(message)
            .cards(cards == null
                ? Collections.emptyList()
                : cards.stream()
                    .map(card -> CardListResponse.CardItem.builder()
                        .cardIssuerName(card.getCardIssuerName())
                        .cardName(card.getCardName())
                        .monthlyCardExpense(calculateMonthlyCardExpense(card))
                        .build())
                    .collect(Collectors.toList()))
            .build();
    }

    private CardTransactionResponse convertToCardTransactionResponse(
        OpenBankCardTransactionResponse response, String cardNoFromPath) {
        boolean success = response != null
            && response.getHeader() != null
            && SUCCESS_CODE.equals(response.getHeader().getResponseCode());

        String code = success ? "TRANSACTION_200_1" : "TRANSACTION_500_1";
        String message = success
            ? "Card transactions retrieved."
            : "Failed to retrieve card transactions.";

        if (response == null || response.getRec() == null) {
            return CardTransactionResponse.builder()
                .success(success)
                .code(code)
                .message(message)
                .cardName(null)
                .cardNo(cardNoFromPath)
                .transaction(Collections.emptyList())
                .build();
        }

        OpenBankCardTransactionResponse.Rec rec = response.getRec();
        String cardNo = rec.getCardNo() != null ? rec.getCardNo() : cardNoFromPath;

        return CardTransactionResponse.builder()
            .success(success)
            .code(code)
            .message(message)
            .cardName(rec.getCardName())
            .cardNo(cardNo)
            .transaction(rec.getTransactionList() == null
                ? Collections.emptyList()
                : rec.getTransactionList().stream()
                    .map(tx -> CardTransactionResponse.TransactionItem.builder()
                        .categoryName(tx.getCategoryName())
                        .merchantName(tx.getMerchantName())
                        .transactionDate(tx.getTransactionDate())
                        .transactionTime(tx.getTransactionTime())
                        .transactionBalance(tx.getTransactionBalance())
                        .build())
                    .collect(Collectors.toList()))
            .build();
    }

    private long calculateMonthlyCardExpense(Card card) {
        long maxBenefitLimit = card.getMaxBenefitLimit() == null ? 0L : card.getMaxBenefitLimit();
        long baselinePerformance =
            card.getBaselinePerformance() == null ? 0L : card.getBaselinePerformance();

        if (maxBenefitLimit <= 0) {
            return 0L;
        }
        if (baselinePerformance <= 0) {
            return Math.round(maxBenefitLimit * 0.6);
        }
        return Math.min(maxBenefitLimit, baselinePerformance);
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

    private CardCredential resolveCardCredential(Long userId, String cardNo) {
        return cardRepository.findByUserIdAndCardNo(userId, cardNo)
            .map(card -> new CardCredential(card.getCardNo(), card.getCvc()))
            .orElseGet(() -> {
                refreshCardsFromExternal(userId);
                return cardRepository.findByUserIdAndCardNo(userId, cardNo)
                    .map(card -> new CardCredential(card.getCardNo(), card.getCvc()))
                    .orElseThrow(() ->
                        new IllegalArgumentException("Card not found for userId=" + userId + ", cardNo=" + cardNo));
            });
    }

    private User getRequiredUserWithFinanceKey(Long userId) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new IllegalArgumentException("User not found: " + userId));

        String financeUserKey = user.getSsafyFinanceUserKey();
        if (financeUserKey == null || financeUserKey.isBlank()) {
            throw new IllegalArgumentException("ssafy_finance_user_key is missing for userId=" + userId);
        }

        return user;
    }

    private String generateUniqueNo(LocalDateTime now) {
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        int randomNo = new Random().nextInt(900000) + 100000;
        return timestamp + randomNo;
    }

    private record CardCredential(String cardNo, String cvc) {
    }

    private record RefreshResult(boolean success, List<Card> cards, String message) {
    }
}
