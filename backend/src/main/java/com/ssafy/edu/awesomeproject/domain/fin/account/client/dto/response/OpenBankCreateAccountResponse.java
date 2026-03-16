package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import lombok.Getter;

/** 외부 은행 API의 계좌 개설 응답을 받기 위한 DTO */
@Getter
public class OpenBankCreateAccountResponse {
    @JsonProperty("Header")
    private OpenBankResHeader header;

    @JsonProperty("REC")
    private Rec rec;

    @Getter
    public static class Rec {
        private String bankCode;
        private String bankName;
        private String userName;
        private String accountNo;
        private String accountName;
        private String accountTypeCode;
        private String accountTypeName;
        private String accountCreatedDate;
        private String accountExpiryDate;
        private String dailyTransferLimit;
        private String oneTimeTransferLimit;
        private String currency;
    }
}
