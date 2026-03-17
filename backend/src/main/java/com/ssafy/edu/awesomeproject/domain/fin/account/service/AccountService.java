package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class AccountService {

    private final OpenBankAdapter openBankAdapter;
    private final AccountRepository accountRepository;
    private final com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository userRepository;

    /** '세이브 박스' 계좌를 신규 개설합니다. (Stateless) */
    public AccountCreateResponse createSaveBox(Long userId, SaveBoxCreateRequest request) {
        com.ssafy.edu.awesomeproject.domain.auth.entity.User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () ->
                                        new IllegalArgumentException(
                                                "사용자를 찾을 수 없습니다. (ID: " + userId + ")"));

        String userKey = user.getSsafyFinanceUserKey();
        if (userKey == null || userKey.isBlank()) {
            throw new IllegalArgumentException("사용자의 Finance User Key가 설정되지 않았습니다.");
        }

        OpenBankCreateAccountResponse apiResponse =
                openBankAdapter.createDemandDepositAccount(userKey, request.accountTypeUniqueNo());

        if (apiResponse == null || apiResponse.getHeader() == null || apiResponse.getRec() == null) {
            throw new RuntimeException("금융 API 응답이 올바르지 않거나 계좌 개설에 실패했습니다.");
        }

        String responseCode = apiResponse.getHeader().getResponseCode();
        if (!"201".equals(responseCode) && !"H0000".equals(responseCode)) {
            String errorMsg = apiResponse.getHeader().getResponseMessage();
            throw new RuntimeException("계좌 개설 실패: " + (errorMsg != null ? errorMsg : "알 수 없는 오류"));
        }

        OpenBankCreateAccountResponse.Rec rec = apiResponse.getRec();

        return AccountCreateResponse.builder()
                .accountNo(rec.getAccountNo())
                .bankCode(rec.getBankCode())
                .bankName("SSAFY Bank")
                .build();
    }

    private BigDecimal parseBigDecimal(String value) {
        if (value == null || value.isBlank()) {
            return BigDecimal.ZERO;
        }
        try {
            String cleaned = value.replaceAll("[^0-9.]", "");
            return new BigDecimal(cleaned);
        } catch (Exception e) {
            return BigDecimal.ZERO;
        }
    }

    @Transactional(readOnly = true)
    public AccountResponse getAccount(Long userId, Long accountId) {
        Account account = accountRepository
                .findById(accountId)
                .filter(a -> a.getUserId().equals(userId))
                .orElseThrow(() -> new IllegalArgumentException("계좌를 찾을 수 없습니다."));

        return AccountResponse.from(account);
    }

    @Transactional(readOnly = true)
    public AccountListResponse getAccountList(Long userId) {
        List<Account> accounts = accountRepository.findAllByUserId(userId);

        List<AccountListResponse.AccountDetail> accountDetails =
                accounts.stream()
                        .map(
                                account ->
                                        new AccountListResponse.AccountDetail(
                                                account.getBankCode(),
                                                account.getBankName(),
                                                account.getUserName(),
                                                account.getAccountNo(),
                                                account.getAccountName(),
                                                account.getAccountTypeCode(),
                                                account.getAccountTypeName(),
                                                account.getAccountCreatedDate() != null ? account.getAccountCreatedDate().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd")) : null,
                                                account.getAccountExpiryDate() != null ? account.getAccountExpiryDate().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd")) : null,
                                                String.valueOf(account.getDailyTransferLimit()),
                                                String.valueOf(account.getOneTimeTransferLimit()),
                                                String.valueOf(account.getBalance()),
                                                account.getLastTransactionDate() != null ? account.getLastTransactionDate().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd")) : null,
                                                account.getCurrencyCode()))
                        .collect(Collectors.toList());

        return new AccountListResponse(accountDetails);
    }

    public AccountListResponse refreshAccountList(Long userId) {
        syncAccounts(userId);
        return getAccountList(userId);
    }

    private void syncAccounts(Long userId) {
        com.ssafy.edu.awesomeproject.domain.auth.entity.User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        String userKey = user.getSsafyFinanceUserKey();
        if (userKey == null || userKey.isBlank()) {
            return;
        }

        // 1. 전체 계좌 목록 조회
        AccountListResponse listResponse = openBankAdapter.fetchDemandDepositAccounts(userKey);
        
        if (listResponse == null || listResponse.accounts() == null) return;

        // 2. 응답 데이터를 DB에 반영 (Upsert)
        for (AccountListResponse.AccountDetail detail : listResponse.accounts()) {
            String accountNo = detail.accountNo();
            Optional<Account> accountOpt = accountRepository.findByAccountNo(accountNo);

            BigDecimal balance = parseBigDecimal(detail.accountBalance());

            if (accountOpt.isPresent()) {
                Account existingAccount = accountOpt.get();
                existingAccount.updateDynamicInfo(detail.accountName(), balance, "ACTIVE");
            } else {
                Account newAccount =
                        Account.builder()
                                .userId(userId)
                                .accountNo(detail.accountNo())
                                .bankName(detail.bankName())
                                .bankCode(detail.bankCode())
                                .accountName(detail.accountName())
                                .currencyCode(detail.currencyCode())
                                .balance(balance)
                                .status("ACTIVE")
                                .isPrimary(false)
                                .accountRole("LINKED_DEPOSIT")
                                .userName(detail.userName())
                                .accountTypeCode(detail.accountTypeCode())
                                .accountTypeName(detail.accountTypeName())
                                .accountCreatedDate(parseLocalDate(detail.accountCreatedDate()))
                                .accountExpiryDate(parseLocalDate(detail.accountExpiryDate()))
                                .dailyTransferLimit(parseBigDecimal(detail.dailyTransferLimit()))
                                .oneTimeTransferLimit(parseBigDecimal(detail.oneTimeTransferLimit()))
                                .lastTransactionDate(parseLocalDate(detail.lastTransactionDate()))
                                .build();

                accountRepository.save(newAccount);
            }
        }
    }

    private java.time.LocalDate parseLocalDate(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) {
            return null;
        }
        try {
            return java.time.LocalDate.parse(
                    dateStr, java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            return null;
        }
    }

    public AccountResponse setPrimaryAccount(Long userId, Long accountId) {
        java.util.List<Account> primaryAccounts = accountRepository.findAll().stream()
                .filter(a -> a.getUserId().equals(userId) && a.isPrimary())
                .toList();

        for (Account a : primaryAccounts) {
            a.unsetPrimary();
        }

        Account account = accountRepository
                .findById(accountId)
                .filter(a -> a.getUserId().equals(userId))
                .orElseThrow(() -> new IllegalArgumentException("계좌를 찾을 수 없습니다."));

        account.setAsPrimary();

        return AccountResponse.from(account);
    }
}
