package com.ssafy.edu.awesomeproject.domain.fin.card.service;

import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request.OpenBankCardTransactionRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankCardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankClient;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.Random;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CardService {

    private static final String SUCCESS_CODE = "H0000";

    //더미로 카드 넣기
    private static final String HARDCODED_CARD_NO = "1002612577288540";
    private static final String HARDCODED_CVC = "521";

    private final OpenBankClient openBankClient;

    @Value("${auth.api.key}")
    private String apiKey;


    // 카드목록 조회 바디
    public CardListResponse getCardList(Long userId) {
        // TODO: Replace with userKey lookup by userId
        String userKey = "31cc0084-6b77-42c9-8927-762488bc2767";

        OpenBankRequest request = createCardListRequest(userKey);
        OpenBankResponse response = openBankClient.fetchCreditCardList(request);

        return convertToCardListResponse(response);
    }

    // 카드 거래내역 조회 바디
    public CardTransactionResponse getCardTransactions(
        Long userId, String cardNo, String startDate, String endDate) {
        // TODO: Replace with userKey lookup by userId
        String userKey = "31cc0084-6b77-42c9-8927-762488bc2767";

        OpenBankCardTransactionRequest request =
            createCardTransactionRequest(userKey, startDate, endDate);
        OpenBankCardTransactionResponse response = openBankClient.fetchCreditCardTransactions(request);

        return convertToCardTransactionResponse(response, cardNo);
    }


    //카드목록 리퀘스트 바디 만들기
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

    //거래내역 리퀘스트 바디만들기
    private OpenBankCardTransactionRequest createCardTransactionRequest(
        String userKey, String startDate, String endDate) {
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
            .cardNo(HARDCODED_CARD_NO)
            .cvc(HARDCODED_CVC)
            .startDate(startDate)
            .endDate(endDate)
            .build();
    }


    //카드목록 응답을 프론트로 보낼 형식으로 바디변환
    private CardListResponse convertToCardListResponse(OpenBankResponse response) {
        boolean success = response != null
            && response.getHeader() != null
            && SUCCESS_CODE.equals(response.getHeader().getResponseCode());

        String code = success ? "TRANSACTION_200_1" : "TRANSACTION_500_1";
        String message = success ? "Card list retrieved." : "Failed to retrieve card list.";

        if (response == null || response.getRec() == null) {
            return CardListResponse.builder()
                .success(success)
                .code(code)
                .message(message)
                .cards(Collections.emptyList())
                .build();
        }

        return CardListResponse.builder()
            .success(success)
            .code(code)
            .message(message)
            .cards(response.getRec().stream()
                .map(card -> CardListResponse.CardItem.builder()
                    .cardIssuerName(card.getCardIssuerName())
                    .cardName(card.getCardName())
                    .monthlyCardExpense(calculateMonthlyCardExpense(card))
                    .build())
                .collect(Collectors.toList()))
            .build();
    }

    //결재내역받은 바디를 프론트로 보낼 바디로 변환
    private CardTransactionResponse convertToCardTransactionResponse(
        OpenBankCardTransactionResponse response, String cardNoFromPath) {
        boolean success = response != null
            && response.getHeader() != null
            && SUCCESS_CODE.equals(response.getHeader().getResponseCode());

        String code = "1231321";
        String message = "계좌의 거래내역을 불러왔습니다.";

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

    //카드목록 보여줄떄 월별 사용금액 보여줘야하는데 날짜를 뭘로하고 보여주지
    // TODO: Replace with real monthly spending aggregation logic.
    private long calculateMonthlyCardExpense(OpenBankResponse.Rec card) {
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

    private String generateUniqueNo(LocalDateTime now) {
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        int randomNo = new Random().nextInt(900000) + 100000;
        return timestamp + randomNo;
    }
}
