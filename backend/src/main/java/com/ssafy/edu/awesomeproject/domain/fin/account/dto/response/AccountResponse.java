package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import java.math.BigDecimal;
import java.time.LocalDate;

/** 계좌 상세 정보를 반환하기 위한 불변 DTO (record) */
public record AccountResponse(
        Long id,
        String bankName,
        String bankCode,
        String accountNo,
        String accountName,
        BigDecimal balance,
        String currencyCode,
        String userName,
        String accountRole,
        String accountTypeName,
        LocalDate accountCreatedDate,
        LocalDate accountExpiryDate,
        BigDecimal dailyTransferLimit,
        BigDecimal oneTimeTransferLimit,
        boolean isPrimary,
        String status) {

    public static AccountResponse from(Account account) {
        return new AccountResponse(
                account.getId(),
                account.getBankName(),
                account.getBankCode(),
                account.getAccountNo(),
                account.getAccountName(),
                account.getBalance(),
                account.getCurrencyCode(),
                account.getUserName(),
                account.getAccountRole(),
                account.getAccountTypeName(),
                account.getAccountCreatedDate(),
                account.getAccountExpiryDate(),
                account.getDailyTransferLimit(),
                account.getOneTimeTransferLimit(),
                account.isPrimary(),
                account.getStatus());
    }
}
