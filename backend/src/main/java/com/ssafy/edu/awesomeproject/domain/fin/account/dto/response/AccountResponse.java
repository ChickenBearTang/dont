package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountStatus;
import java.math.BigDecimal;
import lombok.Builder;


@Builder
public record AccountResponse(
        Long id,
        String bankName,
        String bankCode,
        String accountNo,
        String accountName,
        BigDecimal balance,
        String userName,
        AccountStatus status,
        Boolean isPrimary) {

    public static AccountResponse from(Account account) {
        return AccountResponse.builder()
                .id(account.getId())
                .bankName(account.getBankName())
                .bankCode(account.getBankCode())
                .accountNo(account.getAccountNo())
                .accountName(account.getAccountName())
                .balance(account.getBalance())
                .userName(account.getUserName())
                .status(account.getStatus())
                .isPrimary(account.isPrimary())
                .build();
    }
}
