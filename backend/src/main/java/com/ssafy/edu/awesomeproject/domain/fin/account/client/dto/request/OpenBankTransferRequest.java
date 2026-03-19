package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;

@Builder
public record OpenBankTransferRequest(
        @JsonProperty("Header") OpenBankReqHeader header,
        @JsonProperty("depositAccountNo") String depositAccountNo,
        @JsonProperty("depositTransactionSummary") String depositTransactionSummary,
        @JsonProperty("transactionBalance") String transactionBalance,
        @JsonProperty("withdrawalAccountNo") String withdrawalAccountNo,
        @JsonProperty("withdrawalTransactionSummary") String withdrawalTransactionSummary) {}
