package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import lombok.Getter;

import java.util.List;

@Getter
public class OpenBankResponse {

    // global에서 만든 공통 응답 헤더 객체를 사용
    @JsonProperty("Header")
    private OpenBankResHeader header;

    @JsonProperty("REC")
    private List<Rec> rec;

    @Getter
    public static class Rec {
        private String bankCode;
        private String bankName;
        private String userName;
        private String accountNo;
        private String accountName;
        private String accountBalance;
        private String currency;
    }
}
