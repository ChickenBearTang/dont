package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import java.util.List;

public record AccountListResponse(List<AccountDetail> accounts) {

    public static AccountListResponse from(OpenBankResponse apiResponse) {
        if (apiResponse.rec() == null) {
            return new AccountListResponse(List.of()); // 불변 빈 리스트 반환
        }
        List<AccountDetail> details =
                apiResponse.rec().stream()
                        .map(AccountDetail::from)
                        .toList(); // Java 16+ toList()는 불변 리스트를 반환합니다.
        return new AccountListResponse(details);
    }

    public record AccountDetail(
            String bankName,
            String bankCode,
            String accountNo,
            String accountName,
            String accountBalance,
            String currencyCode) {
        public static AccountDetail from(OpenBankResponse.Rec rec) {
            return new AccountDetail(
                    rec.bankName(),
                    rec.bankCode(),
                    rec.accountNo(),
                    rec.accountName(),
                    rec.accountBalance(),
                    rec.currency());
        }
    }
}
