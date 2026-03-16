package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional // DB에 데이터를 저장/수정하므로 트랜잭션 관리가 필수입니다.
public class AccountService {

    private final OpenBankAdapter openBankAdapter;
    private final AccountRepository accountRepository;

    /**
     * 사용자의 계좌 목록을 조회합니다.
     * 1. 외부 API와 동기화하여 DB를 최신 상태로 만듭니다.
     * 2. 우리 DB에 저장된 계좌 정보를 조회하여 반환합니다.
     */
    public AccountListResponse getAccountList(Long userId) {
        // 1. 외부 API와 동기화 (Command)
        syncAccounts(userId);

        // 2. DB에서 최신 계좌 목록 조회 (Query)
        List<Account> accounts = accountRepository.findAllByUserId(userId);

        // 3. 조회된 엔티티 목록을 DTO로 변환하여 반환
        List<AccountListResponse.AccountDetail> accountDetails = accounts.stream()
            .map(account -> new AccountListResponse.AccountDetail(
                account.getBankName(),
                account.getBankCode(),
                account.getAccountNo(),
                account.getAccountName(),
                String.valueOf(account.getBalance()),
                account.getCurrencyCode()
            ))
            .collect(Collectors.toList());

        return new AccountListResponse(accountDetails);
    }

    /**
     * 외부 API를 통해 계좌 정보를 가져와 DB와 동기화합니다. (Upsert)
     */
    private void syncAccounts(Long userId) {
        String userKey = "31cc0084-6b77-42c9-8927-762488bc2767"; // 임시 userKey
        AccountListResponse apiResponse = openBankAdapter.fetchDemandDepositAccounts(userKey);

        for (AccountListResponse.AccountDetail detail : apiResponse.accounts()) {
            Optional<Account> accountOpt = accountRepository.findByAccountNo(detail.accountNo());

            // String 형태의 잔액을 BigDecimal로 변환
            BigDecimal balance = new BigDecimal(detail.accountBalance());

            if (accountOpt.isPresent()) {
                // 이미 존재하는 계좌는 동적으로 변하는 정보(잔액, 상태 등)를 업데이트합니다.
                Account existingAccount = accountOpt.get();
                existingAccount.updateDynamicInfo(detail.accountName(), balance, "ACTIVE"); // 상태는 예시입니다.
            } else {
                // 새로운 계좌이면 API 응답을 바탕으로 엔티티를 생성하여 저장합니다.
                Account newAccount = Account.builder()
                    .userId(userId)
                    .accountNo(detail.accountNo())
                    .bankName(detail.bankName())
                    .bankCode(detail.bankCode())
                    .accountName(detail.accountName())
                    .currencyCode(detail.currencyCode())
                    .balance(balance) // 초기 잔액 설정
                    .build();
                accountRepository.save(newAccount);
            }
        }
    }
}
