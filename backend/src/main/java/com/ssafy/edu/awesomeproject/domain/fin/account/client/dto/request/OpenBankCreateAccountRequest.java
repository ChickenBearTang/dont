package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class OpenBankCreateAccountRequest {
    @JsonProperty("Header")
    private OpenBankReqHeader header;

    @JsonProperty("accountTypeUniqueNo")
    private String accountTypeUniqueNo;
}
