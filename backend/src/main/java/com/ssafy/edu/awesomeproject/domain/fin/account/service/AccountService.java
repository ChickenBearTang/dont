package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransactionHistoryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransferResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.SavingsSettingResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import java.math.BigDecimal;
import java.util.ArrayList;
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
    private final AccountTransactionRepository accountTransactionRepository;
    private final SavingsSettingRepository savingsSettingRepository;
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

    public AccountTransactionResponse getAccountTransactions(
            Long userId, Long accountId, String startDate, String endDate) {
        Account account =
                accountRepository
                        .findById(accountId)
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(() -> new IllegalArgumentException("계좌를 찾을 수 없습니다."));

        // 1. 거래 내역 동기화 (간편하게 조회 시마다 최신화 시도)
        syncTransactions(userId, account, startDate, endDate);

        // 2. DB에서 거래 내역 조회
        List<AccountTransaction> transactions =
                accountTransactionRepository
                        .findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(accountId);

        return AccountTransactionResponse.builder()
                .accountNo(account.getAccountNo())
                .accountName(account.getAccountName())
                .transactions(
                        transactions.stream()
                                .map(
                                        t ->
                                                AccountTransactionResponse.TransactionItem.builder()
                                                        .transactionUniqueNo(t.getTransactionUniqueNo())
                                                        .transactionDate(
                                                                t.getTransactionDate()
                                                                        .format(
                                                                                java.time.format
                                                                                        .DateTimeFormatter
                                                                                        .ofPattern(
                                                                                                "yyyyMMdd")))
                                                        .transactionTime(t.getTransactionTime())
                                                        .transactionType(t.getTransactionType())
                                                        .transactionTypeName(t.getTransactionTypeName())
                                                        .transactionAmount(
                                                                String.valueOf(t.getTransactionAmount()))
                                                        .afterBalance(String.valueOf(t.getAfterBalance()))
                                                        .transactionSummary(t.getTransactionSummary())
                                                        .transactionMemo(t.getTransactionMemo())
                                                        .build())
                                .collect(Collectors.toList()))
                .build();
    }

    private void syncTransactions(Long userId, Account account, String startDate, String endDate) {
        com.ssafy.edu.awesomeproject.domain.auth.entity.User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        OpenBankTransactionHistoryResponse apiResponse =
                openBankAdapter.fetchTransactionHistory(
                        user.getSsafyFinanceUserKey(),
                        account.getAccountNo(),
                        startDate,
                        endDate,
                        "A", // 전체
                        "DESC"); // 최신순

        if (apiResponse == null || apiResponse.getRec() == null || apiResponse.getRec().getList() == null) {
            return;
        }

        List<AccountTransaction> newTransactions = new ArrayList<>();

        for (OpenBankTransactionHistoryResponse.TransactionItem item : apiResponse.getRec().getList()) {
            if (accountTransactionRepository.findByTransactionUniqueNo(item.getTransactionUniqueNo()).isEmpty()) {
                AccountTransaction transaction =
                        AccountTransaction.builder()
                                .account(account)
                                .transactionUniqueNo(item.getTransactionUniqueNo())
                                .transactionDate(parseLocalDate(item.getTransactionDate()))
                                .transactionTime(item.getTransactionTime())
                                .transactionType(item.getTransactionType())
                                .transactionTypeName(item.getTransactionTypeName())
                                .transactionAccountNo(item.getTransactionAccountNo())
                                .transactionAmount(parseBigDecimal(item.getTransactionBalance())) // API 필드명이 Balance지만 실제론 거래금액임
                                .afterBalance(parseBigDecimal(item.getTransactionAfterBalance()))
                                .transactionSummary(item.getTransactionSummary())
                                .transactionMemo(item.getTransactionMemo())
                                .build();
                accountTransactionRepository.save(transaction);
                newTransactions.add(transaction);
            }
        }

        // 새 거래 내역이 있다면 자동 저축 로직 검토
        if (!newTransactions.isEmpty()) {
            processAutoSavings(userId, account, newTransactions);
        }
    }

    private void processAutoSavings(Long userId, Account primaryAccount, List<AccountTransaction> transactions) {
        // 주계좌인 경우에만 감지
        if (!primaryAccount.isPrimary()) return;

        Optional<SavingsSetting> settingOpt = savingsSettingRepository.findByUserIdAndIsActiveTrue(userId);
        if (settingOpt.isEmpty()) return;

        SavingsSetting setting = settingOpt.get();
        String keyword = setting.getKeyword();

        for (AccountTransaction t : transactions) {
            // 입금('1') 이고, 적요나 메모에 키워드가 포함된 경우
            if ("1".equals(t.getTransactionType()) && 
                ((t.getTransactionSummary() != null && t.getTransactionSummary().contains(keyword)) || 
                 (t.getTransactionMemo() != null && t.getTransactionMemo().contains(keyword)))) {
                
                executeSavingsTransfer(userId, setting);
            }
        }
    }

    private void executeSavingsTransfer(Long userId, SavingsSetting setting) {
        Account primaryAccount = accountRepository.findById(setting.getPrimaryAccountId()).orElse(null);
        Account saveboxAccount = accountRepository.findById(setting.getSaveboxAccountId()).orElse(null);
        
        if (primaryAccount == null || saveboxAccount == null) return;

        com.ssafy.edu.awesomeproject.domain.auth.entity.User user =
                userRepository.findById(userId).orElse(null);
        if (user == null) return;

        OpenBankTransferResponse apiResponse = openBankAdapter.fetchAccountTransfer(
                user.getSsafyFinanceUserKey(),
                saveboxAccount.getAccountNo(),
                "(자동저축) 입금",
                setting.getSavingsAmount().setScale(0, java.math.RoundingMode.DOWN).toString(),
                primaryAccount.getAccountNo(),
                "(자동저축) 출금"
        );
        
        if (apiResponse != null && apiResponse.getHeader() != null) {
            String responseCode = apiResponse.getHeader().getResponseCode();
            if (!"H0000".equals(responseCode)) {
                // 자동 이체 실패 시 로깅하거나 무시할 수 있지만, 일단은 명시적으로 확인
                System.err.println("자동 저축 이체 실패: " + apiResponse.getHeader().getResponseMessage());
                return; // 실패 시 이후 동기화 생략
            }
        }
        
        // 이체 성공 후 로컬 잔액 강제 갱신
        syncAccounts(userId);
    }

    public SavingsSettingResponse createOrUpdateSavingsSetting(Long userId, SavingsSettingRequest request) {
        SavingsSetting setting = savingsSettingRepository.findByUserIdAndIsActiveTrue(userId)
                .orElse(SavingsSetting.builder()
                        .userId(userId)
                        .primaryAccountId(request.primaryAccountId())
                        .saveboxAccountId(request.saveboxAccountId())
                        .keyword(request.keyword())
                        .savingsAmount(request.savingsAmount())
                        .isActive(request.isActive())
                        .build());

        if (setting.getId() != null) {
            setting.update(request.keyword(), request.savingsAmount(), request.isActive());
        }

        SavingsSetting saved = savingsSettingRepository.save(setting);
        return SavingsSettingResponse.builder()
                .id(saved.getId())
                .primaryAccountId(saved.getPrimaryAccountId())
                .saveboxAccountId(saved.getSaveboxAccountId())
                .keyword(saved.getKeyword())
                .savingsAmount(saved.getSavingsAmount())
                .isActive(saved.isActive())
                .build();
    }

    @Transactional(readOnly = true)
    public SavingsSettingResponse getSavingsSetting(Long userId) {
        return savingsSettingRepository.findByUserIdAndIsActiveTrue(userId)
                .map(s -> SavingsSettingResponse.builder()
                        .id(s.getId())
                        .primaryAccountId(s.getPrimaryAccountId())
                        .saveboxAccountId(s.getSaveboxAccountId())
                        .keyword(s.getKeyword())
                        .savingsAmount(s.getSavingsAmount())
                        .isActive(s.isActive())
                        .build())
                .orElse(null);
    }

    public void manualSavings(Long userId, BigDecimal amount) {
        SavingsSetting setting = savingsSettingRepository.findByUserIdAndIsActiveTrue(userId)
                .orElseThrow(() -> new IllegalArgumentException("활성화된 저축 설정이 없습니다. 먼저 설정을 완료해 주세요."));
        
        Account primaryAccount = accountRepository.findById(setting.getPrimaryAccountId())
                .orElseThrow(() -> new IllegalArgumentException("주계좌를 찾을 수 없습니다."));
        Account saveboxAccount = accountRepository.findById(setting.getSaveboxAccountId())
                .orElseThrow(() -> new IllegalArgumentException("세이브박스 계좌를 찾을 수 없습니다."));

        com.ssafy.edu.awesomeproject.domain.auth.entity.User user =
                userRepository.findById(userId).orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));

        System.out.println("수동 저축 실행 시도 - 사용자: " + userId);
        System.out.println("출금 계좌 (주계좌): " + primaryAccount.getAccountNo() + " (ID: " + primaryAccount.getId() + ", 잔액: " + primaryAccount.getBalance() + ")");
        System.out.println("입금 계좌 (세이브박스): " + saveboxAccount.getAccountNo() + " (ID: " + saveboxAccount.getId() + ", 잔액: " + saveboxAccount.getBalance() + ")");
        System.out.println("이체 금액: " + amount);

        OpenBankTransferResponse apiResponse = openBankAdapter.fetchAccountTransfer(
                user.getSsafyFinanceUserKey(),
                saveboxAccount.getAccountNo(),
                "(수동저축) 입금",
                amount.setScale(0, java.math.RoundingMode.DOWN).toString(),
                primaryAccount.getAccountNo(),
                "(수동저축) 출금"
        );

        if (apiResponse == null || apiResponse.getHeader() == null) {
            throw new RuntimeException("금융 API 응답이 없거나 통신에 실패했습니다.");
        }

        String responseCode = apiResponse.getHeader().getResponseCode();
        if (!"H0000".equals(responseCode)) {
            String errorMsg = apiResponse.getHeader().getResponseMessage();
            throw new RuntimeException("이체 실패: " + (errorMsg != null ? errorMsg : "알 수 없는 금융 서버 오류"));
        }

        syncAccounts(userId);
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

        // 저축 설정이 있다면 주계좌 정보를 동기화해줍니다.
        savingsSettingRepository.findByUserIdAndIsActiveTrue(userId)
                .ifPresent(setting -> setting.updatePrimaryAccount(accountId));

        return AccountResponse.from(account);
    }
}
