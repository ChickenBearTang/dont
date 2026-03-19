package com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import java.util.List;
import lombok.Getter;

@Getter
public class OpenBankResponse {

    @JsonProperty("Header")
    private OpenBankResHeader header;

    @JsonProperty("REC")
    private List<Rec> rec;

    @Getter
    public static class Rec {
        private String cardNo;
        private String cvc;
        private String cardUniqueNo;
        private String cardIssuerCode;
        private String cardIssuerName;
        private String cardName;
        private Long baselinePerformance;
        private Long maxBenefitLimit;
        private String cardDescription;
        private String cardExpiryDate;
        private String withdrawalAccountNo;
        private String withdrawalDate;
    }
}
