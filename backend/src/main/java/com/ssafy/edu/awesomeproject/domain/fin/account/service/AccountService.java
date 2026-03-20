package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
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
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountStatus;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.response.OpenBankDetailAccountResponse;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class AccountService {

    private final OpenBankAdapter openBankAdapter;
    private final AccountRepository accountRepository;
    private final AccountTransactionRepository accountTransactionRepository;
    private final SavingsSettingRepository savingsSettingRepository;
    private final UserRepository userRepository;

    public AccountCreateResponse createSaveBox(Long userId, SaveBoxCreateRequest request) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));

        String userKey = user.getSsafyFinanceUserKey();
        if (userKey == null || userKey.isBlank()) {
            throw new AccountException(AccountErrorCode.FINANCE_USER_KEY_NOT_FOUND);
        }

        OpenBankCreateAccountResponse apiResponse =
                openBankAdapter.createDemandDepositAccount(userKey, request.accountTypeUniqueNo());

        if (apiResponse == null
                || apiResponse.getHeader() == null
                || apiResponse.getRec() == null) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }

        String responseCode = apiResponse.getHeader().getResponseCode();
        if (!"201".equals(responseCode) && !"H0000".equals(responseCode)) {
            throw new AccountException(
                    AccountErrorCode.API_RESPONSE_ERROR,
                    apiResponse.getHeader().getResponseMessage());
        }

        OpenBankCreateAccountResponse.Rec rec = apiResponse.getRec();

        try {
            OpenBankDetailAccountResponse detailResponse =
                    openBankAdapter.fetchAccountDetail(userKey, rec.getAccountNo());
            if (detailResponse != null && detailResponse.rec() != null) {
                OpenBankDetailAccountResponse.Rec detail = detailResponse.rec();
                Account newAccount =
                        Account.builder()
                                .userId(userId)
                                .accountNo(detail.accountNo())
                                .bankName(detail.bankName())
                                .bankCode(detail.bankCode())
                                .accountName(detail.accountName())
                                .currencyCode(
                                        detail.currency() != null
                                                ? detail.currency().currency()
                                                : "KRW")
                                .balance(parseBigDecimal(detail.accountBalance()))
                                .status(AccountStatus.ACTIVE)
                                .isPrimary(false)
                                .accountRole(AccountRole.SAVE_BOX)
                                .userName(detail.userName())
                                .accountTypeCode(detail.accountTypeCode())
                                .accountTypeName(detail.accountTypeName())
                                .accountCreatedDate(parseLocalDate(detail.accountCreatedDate()))
                                .accountExpiryDate(parseLocalDate(detail.accountExpiryDate()))
                                .dailyTransferLimit(parseBigDecimal(detail.dailyTransferLimit()))
                                .oneTimeTransferLimit(
                                        parseBigDecimal(detail.oneTimeTransferLimit()))
                                .lastTransactionDate(parseLocalDate(detail.lastTransactionDate()))
                                .build();
                accountRepository.save(newAccount);
                log.info("세이브박스 DB 저장 완료: {}", rec.getAccountNo());
            }
        } catch (Exception e) {
            log.error("세이브박스 DB 저장 중 오류 발생 (계좌는 생성됨): {}", e.getMessage());
        }

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
        Account account =
                accountRepository
                        .findById(accountId)
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(
                                () -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));

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
                                                account.getId(),
                                                account.getBankCode(),
                                                account.getBankName(),
                                                account.getUserName(),
                                                account.getAccountNo(),
                                                account.getAccountName(),
                                                account.getAccountTypeCode(),
                                                account.getAccountTypeName(),
                                                account.getAccountCreatedDate() != null
                                                        ? account.getAccountCreatedDate()
                                                                .format(
                                                                        DateTimeFormatter.ofPattern(
                                                                                "yyyyMMdd"))
                                                        : null,
                                                account.getAccountExpiryDate() != null
                                                        ? account.getAccountExpiryDate()
                                                                .format(
                                                                        DateTimeFormatter.ofPattern(
                                                                                "yyyyMMdd"))
                                                        : null,
                                                String.valueOf(account.getDailyTransferLimit()),
                                                String.valueOf(account.getOneTimeTransferLimit()),
                                                String.valueOf(account.getBalance()),
                                                account.getLastTransactionDate() != null
                                                        ? account.getLastTransactionDate()
                                                                .format(
                                                                        DateTimeFormatter.ofPattern(
                                                                                "yyyyMMdd"))
                                                        : null,
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
                        .orElseThrow(
                                () -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));

        syncTransactions(userId, account, startDate, endDate);

        LocalDate start = parseLocalDate(startDate);
        LocalDate end = parseLocalDate(endDate);

        List<AccountTransaction> transactions;
        if (start != null && end != null) {
            transactions =
                    accountTransactionRepository
                            .findAllByAccountIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                    accountId, start, end);
        } else {
            transactions =
                    accountTransactionRepository
                            .findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(
                                    accountId);
        }

        return AccountTransactionResponse.builder()
                .accountNo(account.getAccountNo())
                .accountName(account.getAccountName())
                .transactions(
                        transactions.stream()
                                .map(
                                        t ->
                                                AccountTransactionResponse.TransactionItem.builder()
                                                        .transactionUniqueNo(
                                                                t.getTransactionUniqueNo())
                                                        .transactionDate(
                                                                t.getTransactionDate()
                                                                        .format(
                                                                                DateTimeFormatter
                                                                                        .ofPattern(
                                                                                                "yyyyMMdd")))
                                                        .transactionTime(t.getTransactionTime())
                                                        .transactionType(t.getTransactionType())
                                                        .transactionTypeName(
                                                                t.getTransactionTypeName())
                                                        .transactionAmount(
                                                                String.valueOf(
                                                                        t.getTransactionAmount()))
                                                        .afterBalance(
                                                                String.valueOf(t.getAfterBalance()))
                                                        .transactionSummary(
                                                                t.getTransactionSummary())
                                                        .transactionMemo(t.getTransactionMemo())
                                                        .build())
                                .collect(Collectors.toList()))
                .build();
    }

    private void syncTransactions(Long userId, Account account, String startDate, String endDate) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));

        OpenBankTransactionHistoryResponse apiResponse =
                openBankAdapter.fetchTransactionHistory(
                        user.getSsafyFinanceUserKey(),
                        account.getAccountNo(),
                        startDate,
                        endDate,
                        "A",
                        "DESC");

        if (apiResponse == null
                || apiResponse.getRec() == null
                || apiResponse.getRec().getList() == null) {
            return;
        }

        List<AccountTransaction> newTransactions = new ArrayList<>();

        for (OpenBankTransactionHistoryResponse.TransactionItem item :
                apiResponse.getRec().getList()) {
            if (accountTransactionRepository
                    .findByTransactionUniqueNo(item.getTransactionUniqueNo())
                    .isEmpty()) {
                AccountTransaction transaction =
                        AccountTransaction.builder()
                                .account(account)
                                .transactionUniqueNo(item.getTransactionUniqueNo())
                                .transactionDate(parseLocalDate(item.getTransactionDate()))
                                .transactionTime(item.getTransactionTime())
                                .transactionType(item.getTransactionType())
                                .transactionTypeName(item.getTransactionTypeName())
                                .transactionAccountNo(item.getTransactionAccountNo())
                                .transactionAmount(parseBigDecimal(item.getTransactionBalance()))
                                .afterBalance(parseBigDecimal(item.getTransactionAfterBalance()))
                                .transactionSummary(item.getTransactionSummary())
                                .transactionMemo(item.getTransactionMemo())
                                .build();
                accountTransactionRepository.save(transaction);
                newTransactions.add(transaction);
            }
        }

        if (!newTransactions.isEmpty()) {
            processAutoSavings(userId, account, newTransactions);
        }
    }

    private void processAutoSavings(
            Long userId, Account primaryAccount, List<AccountTransaction> transactions) {
        if (!primaryAccount.isPrimary()) return;

        Optional<SavingsSetting> settingOpt =
                savingsSettingRepository.findByUserIdAndIsActiveTrue(userId);
        if (settingOpt.isEmpty()) return;

        SavingsSetting setting = settingOpt.get();
        String keyword = setting.getKeyword();

        for (AccountTransaction t : transactions) {
            if ("1".equals(t.getTransactionType())
                    && ((t.getTransactionSummary() != null
                                    && t.getTransactionSummary().contains(keyword))
                            || (t.getTransactionMemo() != null
                                    && t.getTransactionMemo().contains(keyword)))) {

                executeSavingsTransfer(userId, setting);
            }
        }
    }

    private void executeSavingsTransfer(Long userId, SavingsSetting setting) {
        Account primaryAccount =
                accountRepository.findById(setting.getPrimaryAccountId()).orElse(null);
        Account saveboxAccount =
                accountRepository.findById(setting.getSaveboxAccountId()).orElse(null);

        if (primaryAccount == null || saveboxAccount == null) return;

        com.ssafy.edu.awesomeproject.domain.auth.entity.User user =
                userRepository.findById(userId).orElse(null);
        if (user == null) return;

        OpenBankTransferResponse apiResponse =
                openBankAdapter.fetchAccountTransfer(
                        user.getSsafyFinanceUserKey(),
                        saveboxAccount.getAccountNo(),
                        "(자동저축) 입금",
                        setting.getSavingsAmount().setScale(0, RoundingMode.DOWN).toString(),
                        primaryAccount.getAccountNo(),
                        "(자동저축) 출금");

        if (apiResponse != null && apiResponse.getHeader() != null) {
            String responseCode = apiResponse.getHeader().getResponseCode();
            if (!"H0000".equals(responseCode)) {
                log.error("자동 저축 이체 실패: {}", apiResponse.getHeader().getResponseMessage());
                return;
            }
        }

        syncAccounts(userId);
    }

    public SavingsSettingResponse createOrUpdateSavingsSetting(
            Long userId, SavingsSettingRequest request) {
        accountRepository
                .findById(request.primaryAccountId())
                .filter(a -> a.getUserId().equals(userId))
                .orElseThrow(() -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));

        accountRepository
                .findById(request.saveboxAccountId())
                .filter(a -> a.getUserId().equals(userId))
                .orElseThrow(() -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));

        SavingsSetting setting =
                savingsSettingRepository
                        .findByUserIdAndIsActiveTrue(userId)
                        .orElse(
                                SavingsSetting.builder()
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
        return savingsSettingRepository
                .findByUserIdAndIsActiveTrue(userId)
                .map(
                        s ->
                                SavingsSettingResponse.builder()
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
        SavingsSetting setting =
                savingsSettingRepository
                        .findByUserIdAndIsActiveTrue(userId)
                        .orElseThrow(
                                () ->
                                        new AccountException(
                                                AccountErrorCode.SAVINGS_SETTING_NOT_FOUND));

        Account primaryAccount =
                accountRepository
                        .findById(setting.getPrimaryAccountId())
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(
                                () ->
                                        new AccountException(
                                                AccountErrorCode.PRIMARY_ACCOUNT_NOT_FOUND));

        Account saveboxAccount =
                accountRepository
                        .findById(setting.getSaveboxAccountId())
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(
                                () ->
                                        new AccountException(
                                                AccountErrorCode.SAVEBOX_ACCOUNT_NOT_FOUND));

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));

        log.info("수동 저축 실행 시도 - 사용자: {}", userId);
        log.info(
                "출금 계좌 (주계좌): {} (ID: {}, 잔액: {})",
                primaryAccount.getAccountNo(),
                primaryAccount.getId(),
                primaryAccount.getBalance());
        log.info(
                "입금 계좌 (세이브박스): {} (ID: {}, 잔액: {})",
                saveboxAccount.getAccountNo(),
                saveboxAccount.getId(),
                saveboxAccount.getBalance());
        log.info("이체 금액: {}", amount);

        OpenBankTransferResponse apiResponse =
                openBankAdapter.fetchAccountTransfer(
                        user.getSsafyFinanceUserKey(),
                        saveboxAccount.getAccountNo(),
                        "(수동저축) 입금",
                        amount.setScale(0, RoundingMode.DOWN).toString(),
                        primaryAccount.getAccountNo(),
                        "(수동저축) 출금");

        if (apiResponse == null || apiResponse.getHeader() == null) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }

        String responseCode = apiResponse.getHeader().getResponseCode();
        if (!"H0000".equals(responseCode)) {
            throw new AccountException(
                    AccountErrorCode.API_RESPONSE_ERROR,
                    apiResponse.getHeader().getResponseMessage());
        }

        syncAccounts(userId);
    }

    private void syncAccounts(Long userId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));

        String userKey = user.getSsafyFinanceUserKey();
        if (userKey == null || userKey.isBlank()) {
            return;
        }

        AccountListResponse listResponse = openBankAdapter.fetchDemandDepositAccounts(userKey);

        if (listResponse == null || listResponse.accounts() == null) return;

        for (AccountListResponse.AccountDetail detail : listResponse.accounts()) {
            String accountNo = detail.accountNo();
            Optional<Account> accountOpt = accountRepository.findByAccountNo(accountNo);

            BigDecimal balance = parseBigDecimal(detail.accountBalance());

            if (accountOpt.isPresent()) {
                Account existingAccount = accountOpt.get();
                existingAccount.updateDynamicInfo(
                        detail.accountName(), balance, AccountStatus.ACTIVE);
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
                                .status(AccountStatus.ACTIVE)
                                .isPrimary(false)
                                .accountRole(AccountRole.LINKED_DEPOSIT)
                                .userName(detail.userName())
                                .accountTypeCode(detail.accountTypeCode())
                                .accountTypeName(detail.accountTypeName())
                                .accountCreatedDate(parseLocalDate(detail.accountCreatedDate()))
                                .accountExpiryDate(parseLocalDate(detail.accountExpiryDate()))
                                .dailyTransferLimit(parseBigDecimal(detail.dailyTransferLimit()))
                                .oneTimeTransferLimit(
                                        parseBigDecimal(detail.oneTimeTransferLimit()))
                                .lastTransactionDate(parseLocalDate(detail.lastTransactionDate()))
                                .build();

                accountRepository.save(newAccount);
            }
        }
    }

    private LocalDate parseLocalDate(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) {
            return null;
        }
        try {
            return LocalDate.parse(dateStr, DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            return null;
        }
    }

    public AccountResponse setPrimaryAccount(Long userId, Long accountId) {
        List<Account> primaryAccounts =
                accountRepository.findAllByUserId(userId).stream()
                        .filter(Account::isPrimary)
                        .toList();

        for (Account a : primaryAccounts) {
            a.unsetPrimary();
        }

        Account account =
                accountRepository
                        .findById(accountId)
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(
                                () -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));

        account.setAsPrimary();

        savingsSettingRepository
                .findByUserIdAndIsActiveTrue(userId)
                .ifPresent(setting -> setting.updatePrimaryAccount(accountId));

        return AccountResponse.from(account);
    }
}
