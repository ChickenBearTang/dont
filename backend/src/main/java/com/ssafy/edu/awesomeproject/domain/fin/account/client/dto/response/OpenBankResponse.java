package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import java.util.List;

public record OpenBankResponse(
        @JsonProperty("Header") OpenBankResHeader header, @JsonProperty("REC") List<Rec> rec) {

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
            String currency) {}
}
