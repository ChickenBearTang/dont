package com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class OpenBankCardTransactionRequest {

    @JsonProperty("Header")
    private OpenBankReqHeader header;

    private String cardNo;
    private String cvc;
    private String startDate;
    private String endDate;
}
