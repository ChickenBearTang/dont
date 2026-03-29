package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import java.util.List;
import lombok.Builder;

public record AccountListResponse(List<AccountDetail> accounts) {

    public static AccountListResponse from(OpenBankResponse apiResponse) {
        if (apiResponse.rec() == null) {
            return new AccountListResponse(List.of());
        }
        List<AccountDetail> details = apiResponse.rec().stream().map(AccountDetail::from).toList();
        return new AccountListResponse(details);
    }

    @Builder
    public record AccountDetail(
            Long id,
            String bankCode,
            String bankName,
            String userName,
            String accountNo,
            String accountName,
            String accountTypeCode,
            String accountTypeName,
            String accountCreatedDate,
            String accountExpiryDate,
            String dailyTransferLimit,
            String oneTimeTransferLimit,
            String accountBalance,
            String lastTransactionDate,
            String currencyCode,
            Boolean isPrimary) {
        public static AccountDetail from(OpenBankResponse.Rec rec) {
            return AccountDetail.builder()
                    .bankCode(rec.bankCode())
                    .bankName(rec.bankName())
                    .userName(rec.userName())
                    .accountNo(rec.accountNo())
                    .accountName(rec.accountName())
                    .accountTypeCode(rec.accountTypeCode())
                    .accountTypeName(rec.accountTypeName())
                    .accountCreatedDate(rec.accountCreatedDate())
                    .accountExpiryDate(rec.accountExpiryDate())
                    .dailyTransferLimit(rec.dailyTransferLimit())
                    .oneTimeTransferLimit(rec.oneTimeTransferLimit())
                    .accountBalance(rec.accountBalance())
                    .lastTransactionDate(rec.lastTransactionDate())
                    .currencyCode(rec.currency())
                    .isPrimary(false)
                    .build();
        }
    }
}
