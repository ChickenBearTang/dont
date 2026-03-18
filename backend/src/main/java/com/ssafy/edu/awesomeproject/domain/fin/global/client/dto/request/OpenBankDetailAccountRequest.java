package com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;
import lombok.Getter;

/** 외부 은행 API의 '계좌 상세 조회' 요청을 위한 DTO */
@Getter
@Builder
public class OpenBankDetailAccountRequest {
    @JsonProperty("Header")
    private OpenBankReqHeader header;

    @JsonProperty("accountNo")
    private String accountNo;
}
