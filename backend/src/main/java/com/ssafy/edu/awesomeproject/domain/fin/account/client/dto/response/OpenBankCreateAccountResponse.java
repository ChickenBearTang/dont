package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class OpenBankCreateAccountResponse {
    @JsonProperty("Header")
    @JsonAlias("header")
    private OpenBankResHeader header;

    @JsonProperty("REC")
    @JsonAlias("rec")
    private Rec rec;

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Rec {
        @JsonAlias({"BankCode", "bankCode"})
        private String bankCode;

        @JsonAlias({"AccountNo", "accountNo"})
        private String accountNo;

        @JsonAlias({"Currency", "currency"})
        private Currency currency;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Currency {
        @JsonAlias("currency")
        private String currency;

        @JsonAlias("currencyName")
        private String currencyName;
    }
}
