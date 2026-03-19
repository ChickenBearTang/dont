package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class OpenBankTransferResponse {

    @JsonProperty("Header")
    private Header header;

    @JsonProperty("REC")
    private List<Rec> rec;

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
        private String transactionUniqueNo;
        private String accountNo;
        private String transactionDate;
        private String transactionType;
        private String transactionTypeName;
        private String transactionAccountNo;
    }
}
