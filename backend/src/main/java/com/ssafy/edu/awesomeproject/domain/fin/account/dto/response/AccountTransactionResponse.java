package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import java.util.List;
import lombok.Builder;

@Builder
public record AccountTransactionResponse(
        String accountNo, String accountName, List<TransactionItem> transactions) {

    @Builder
    public record TransactionItem(
            String transactionUniqueNo,
            String transactionDate,
            String transactionTime,
            String transactionType, // 1: 입금, 2: 출금
            String transactionTypeName,
            String transactionAmount,
            String afterBalance,
            String transactionSummary,
            String transactionMemo) {}
}
