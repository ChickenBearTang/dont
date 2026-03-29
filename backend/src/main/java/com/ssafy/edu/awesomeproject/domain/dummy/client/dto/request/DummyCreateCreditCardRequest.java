package com.ssafy.edu.awesomeproject.domain.dummy.client.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;

@Builder
public record DummyCreateCreditCardRequest(
        @JsonProperty("Header") OpenBankReqHeader header,
        String cardUniqueNo,
        String withdrawalAccountNo,
        String withdrawalDate) {}
