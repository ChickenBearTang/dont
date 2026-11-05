package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import lombok.Builder;

public record AccountListResponse(List<AccountDetail> accounts) {

    private static final DateTimeFormatter BASIC_DATE = DateTimeFormatter.BASIC_ISO_DATE;

    public static AccountListResponse of(List<Account> accounts) {
        return new AccountListResponse(accounts.stream().map(AccountDetail::from).toList());
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

        public static AccountDetail from(Account account) {
            return AccountDetail.builder()
                    .id(account.getId())
                    .bankCode(account.getBankCode())
                    .bankName(account.getBankName())
                    .userName(account.getUserName())
                    .accountNo(account.getAccountNo())
                    .accountName(account.getAccountName())
                    .accountTypeCode(account.getAccountTypeCode())
                    .accountTypeName(account.getAccountTypeName())
                    .accountCreatedDate(format(account.getAccountCreatedDate()))
                    .accountExpiryDate(format(account.getAccountExpiryDate()))
                    .dailyTransferLimit(String.valueOf(account.getDailyTransferLimit()))
                    .oneTimeTransferLimit(String.valueOf(account.getOneTimeTransferLimit()))
                    .accountBalance(String.valueOf(account.getBalance()))
                    .lastTransactionDate(format(account.getLastTransactionDate()))
                    .currencyCode(account.getCurrencyCode())
                    .isPrimary(account.isPrimary())
                    .build();
        }

        private static String format(LocalDate date) {
            return date == null ? null : date.format(BASIC_DATE);
        }
    }
}
