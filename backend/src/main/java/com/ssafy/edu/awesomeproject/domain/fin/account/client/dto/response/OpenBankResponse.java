package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import java.util.List;

public record OpenBankResponse(
        // global에서 만든 공통 응답 헤더 객체를 사용
        @JsonProperty("Header") OpenBankResHeader header, @JsonProperty("REC") List<Rec> rec) {

    public record Rec(
            String bankCode,
            String bankName,
            String userName,
            String accountNo,
            String accountName,
            String accountBalance,
            String currency) {}
}
