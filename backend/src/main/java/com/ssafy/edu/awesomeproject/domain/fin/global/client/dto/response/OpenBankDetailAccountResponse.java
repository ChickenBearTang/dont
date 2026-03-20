package com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;

public record OpenBankDetailAccountResponse(
        @JsonProperty("Header") OpenBankResHeader header, @JsonProperty("REC") Rec rec) {
    public record Rec(
            String bankCode,
            String bankName,
            String userName,
            String accountNo,
            String accountName,
            String accountTypeCode,
            String accountTypeName,
            String accountCreatedDate,
            String accountExpiryDate,
            String dailyTransferLimit,
            String oneTimeTransferLimit,
            String accountBalance,
            String lastTransactionDate,
            Currency currency) {}

    public record Currency(String currency, String currencyName) {}
}
