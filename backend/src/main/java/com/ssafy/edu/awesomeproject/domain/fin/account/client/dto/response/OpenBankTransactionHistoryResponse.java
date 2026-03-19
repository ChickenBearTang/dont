package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class OpenBankTransactionHistoryResponse {

    @JsonProperty("Header")
    private Header header;

    @JsonProperty("REC")
    private Rec rec;

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Header {
        private String responseCode;
        private String responseMessage;
        private String apiName;
        private String transmissionDate;
        private String transmissionTime;
        private String institutionCode;
        private String apiKey;
        private String apiServiceCode;
        private String institutionTransactionUniqueNo;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Rec {
        private String totalCount;
        private List<TransactionItem> list;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TransactionItem {
        private String transactionUniqueNo;
        private String transactionDate;
        private String transactionTime;
        private String transactionType;
        private String transactionTypeName;
        private String transactionAccountNo;
        private String transactionBalance;
        private String transactionAfterBalance;
        private String transactionSummary;
        private String transactionMemo;
    }
}
