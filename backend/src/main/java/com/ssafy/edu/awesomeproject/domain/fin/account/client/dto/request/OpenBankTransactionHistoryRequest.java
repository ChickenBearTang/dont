package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;

@Builder
public record OpenBankTransactionHistoryRequest(
        @JsonProperty("Header") OpenBankReqHeader header,
        String accountNo,
        String startDate,
        String endDate,
        String transactionType,
        String orderByType) {}
