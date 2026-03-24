package com.ssafy.edu.awesomeproject.domain.fin.card.dto.response;

import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class CardTransactionResponse {

    private boolean success;
    private String code;
    private String message;
    private String cardName;
    private String cardNo;
    private List<TransactionItem> transaction;

    @Getter
    @Builder
    public static class TransactionItem {
        private Long id;
        private String categoryName;
        private String merchantName;
        private String transactionDate;
        private String transactionTime;
        private String transactionAmount;
    }
}
