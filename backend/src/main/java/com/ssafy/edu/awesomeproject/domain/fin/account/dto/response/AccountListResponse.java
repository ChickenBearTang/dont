package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import java.util.List;

public record AccountListResponse(List<AccountDetail> accounts) {

    public static AccountListResponse from(OpenBankResponse apiResponse) {
        if (apiResponse.rec() == null) {
            return new AccountListResponse(List.of());
        }
        List<AccountDetail> details =
                apiResponse.rec().stream()
                        .map(AccountDetail::from)
                        .toList();
        return new AccountListResponse(details);
    }

    public record AccountDetail(
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
            String currencyCode) {
        public static AccountDetail from(OpenBankResponse.Rec rec) {
            return new AccountDetail(
                    rec.bankCode(),
                    rec.bankName(),
                    rec.userName(),
                    rec.accountNo(),
                    rec.accountName(),
                    rec.accountTypeCode(),
                    rec.accountTypeName(),
                    rec.accountCreatedDate(),
                    rec.accountExpiryDate(),
                    rec.dailyTransferLimit(),
                    rec.oneTimeTransferLimit(),
                    rec.accountBalance(),
                    rec.lastTransactionDate(),
                    rec.currency());
        }
    }
}
