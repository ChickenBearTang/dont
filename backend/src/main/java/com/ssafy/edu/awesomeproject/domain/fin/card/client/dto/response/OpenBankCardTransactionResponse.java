package com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import java.util.List;
import lombok.Getter;

@Getter
public class OpenBankCardTransactionResponse {

    @JsonProperty("Header")
    private OpenBankResHeader header;

    @JsonProperty("REC")
    private Rec rec;

    @Getter
    public static class Rec {
        private String cardIssuerCode;
        private String cardIssuerName;
        private String cardName;
        private String cardNo;
        private Long estimatedBalance;
        private List<TransactionItem> transactionList;
    }

    @Getter
    public static class TransactionItem {
        private String transactionUniqueNo;
        private String categoryId;
        private String categoryName;
        private String merchantId;
        private String merchantName;
        private String transactionDate;
        private String transactionTime;
        private String transactionBalance;
        private String cardStatus;
        private String billStatementsYn;
        private String billStatementsStatus;
    }
}
