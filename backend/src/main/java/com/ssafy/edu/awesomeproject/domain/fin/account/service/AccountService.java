package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
                String.valueOf(account.getBalance()), // Long을 String으로 변환
                account.getCurrency()
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

            // String 형태의 잔액을 Long으로 변환
            long balance = Long.parseLong(detail.accountBalance());

            if (accountOpt.isPresent()) {
                accountOpt.get().updateInfo(detail.accountName(), balance, detail.currency()); // 이제 currency()가 존재합니다.
            } else {
                Account newAccount = Account.builder()
                    .userId(userId)
                    .accountNo(detail.accountNo())
                    .bankName(detail.bankName())
                    .bankCode(detail.bankCode()) // 이제 bankCode()가 존재합니다.
                    .accountName(detail.accountName())
                    .currency(detail.currency())
                    .build();
                accountRepository.save(newAccount).updateInfo(detail.accountName(), balance, detail.currency());
            }
        }
    }
}
