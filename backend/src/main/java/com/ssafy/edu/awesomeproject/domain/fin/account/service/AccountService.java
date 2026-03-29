package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.LoginService;
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
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import com.ssafy.edu.awesomeproject.domain.ranking.event.SaveboxBalanceUpdatedEvent;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.NumberFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

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
    private final LoginService loginService;
    private final ApplicationEventPublisher eventPublisher;
    private final NotificationService notificationService;

    private final ConcurrentHashMap<Long, Lock> userLocks = new ConcurrentHashMap<>();


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

                Integer cohortNo = user.getCohort() != null ? user.getCohort().getGenerationNo() : null;
                eventPublisher.publishEvent(
                        new SaveboxBalanceUpdatedEvent(
                                userId, newAccount.getBalance().longValue(), cohortNo));
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
                                                account.getCurrencyCode(),
                                                account.isPrimary()))
                        .collect(Collectors.toList());

        return new AccountListResponse(accountDetails);
    }


    public AccountListResponse refreshAccountList(Long userId) {
        syncAccounts(userId);

        List<Account> accounts = accountRepository.findAllByUserId(userId);
        for (Account account : accounts) {
            try {
                String startDate =
                        LocalDate.now()
                                .minusMonths(3)
                                .format(DateTimeFormatter.ofPattern("yyyyMMdd"));
                String endDate = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
                syncTransactions(userId, account, startDate, endDate);
            } catch (Exception e) {
                log.warn(
                        "새로고침 중 거래 내역 동기화 실패 - 계좌: {}, 사유: {}",
                        account.getAccountNo(),
                        e.getMessage());
            }
        }

        return getAccountList(userId);
    }

    public boolean forcePublishSaveboxEvent(Long userId) {
        List<Account> allAccounts = accountRepository.findAllByUserId(userId);
        List<Account> saveboxes = allAccounts.stream()
                .filter(a -> a.getAccountRole() == AccountRole.SAVE_BOX)
                .collect(Collectors.toList());

        if (saveboxes.isEmpty()) {
            List<Account> ssafyBankAccounts = allAccounts.stream()
                    .filter(a -> a.getAccountRole() == AccountRole.LINKED_DEPOSIT)
                    .filter(a -> a.getBankName() != null &&
                                 (a.getBankName().contains("싸피") || a.getBankName().contains("SSAFY")))
                    .sorted((a1, a2) -> a2.getId().compareTo(a1.getId()))
                    .collect(Collectors.toList());
            if (!ssafyBankAccounts.isEmpty()) {
                Account promo = ssafyBankAccounts.get(0);
                promo.updateAccountRole(AccountRole.SAVE_BOX);
                accountRepository.save(promo);
                saveboxes.add(promo);
                log.info("더미 테스트용: '싸피은행' 계좌 중 최신 계좌 {}를 SAVE_BOX로 임의 승격했습니다.", promo.getAccountNo());
            } else {
                return false;
            }
        }

        User user = userRepository.findById(userId).orElse(null);
        Integer cohortNo = (user != null && user.getCohort() != null) ? user.getCohort().getGenerationNo() : null;

        for (Account savebox : saveboxes) {
            eventPublisher.publishEvent(
                    new SaveboxBalanceUpdatedEvent(userId, savebox.getBalance().longValue(), cohortNo));
        }
        return true;
    }


    @Transactional
    public AccountListResponse linkFinanceAccount(Long userId, String userKey) {
        if (userRepository.existsBySsafyFinanceUserKey(userKey)) {
            throw new AccountException(AccountErrorCode.DUPLICATE_FINANCE_KEY);
        }

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
        user.updateSsafyFinanceUserKey(userKey);

        syncAccounts(userId);

        List<Account> accounts = accountRepository.findAllByUserId(userId);
        for (Account account : accounts) {
            try {
                String startDate =
                        LocalDate.now()
                                .minusMonths(3)
                                .format(DateTimeFormatter.ofPattern("yyyyMMdd"));
                String endDate = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
                syncTransactions(userId, account, startDate, endDate);
            } catch (Exception e) {
                log.warn(
                        "초기 거래 내역 동기화 실패 - 계좌: {}, 사유: {}", account.getAccountNo(), e.getMessage());
            }
        }

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

        String defaultStart =
                LocalDate.now().minusMonths(3).format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String defaultEnd = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));

        String normalizedStart = startDate != null ? startDate.replaceAll("-", "") : defaultStart;
        String normalizedEnd = endDate != null ? endDate.replaceAll("-", "") : defaultEnd;

        log.info(
                "거래 내역 조회 요청 - 계좌: {}, 기간: {} ~ {}",
                account.getAccountNo(),
                normalizedStart,
                normalizedEnd);

        syncTransactions(userId, account, normalizedStart, normalizedEnd);

        LocalDate start = parseLocalDate(normalizedStart);
        LocalDate end = parseLocalDate(normalizedEnd);

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
        Lock lock = userLocks.computeIfAbsent(userId, k -> new ReentrantLock());
        lock.lock();
        try {
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
            log.warn("거래 내역 API 응답이 비어있습니다. 계좌: {}", account.getAccountNo());
            return;
        }

        log.info(
                "거래 내역 동기화 시작 - 계좌: {}, 가져온 내역 수: {}",
                account.getAccountNo(),
                apiResponse.getRec().getList().size());

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
            }
        }


        List<AccountTransaction> unprocessed =
                accountTransactionRepository.findAllByAccountIdAndAutoSavingsProcessedFalse(
                        account.getId());
        if (!unprocessed.isEmpty()) {
            processAutoSavings(userId, account, unprocessed);
        }
        } finally {
            if (TransactionSynchronizationManager.isActualTransactionActive()) {
                TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                    @Override
                    public void afterCompletion(int status) {
                        lock.unlock();
                    }
                });
            } else {
                lock.unlock();
            }
        }
    }

    private void processAutoSavings(
            Long userId, Account primaryAccount, List<AccountTransaction> transactions) {

        if (!primaryAccount.isPrimary()) {
            return;
        }

        Optional<SavingsSetting> settingOpt =
                savingsSettingRepository.findByUserIdAndIsActiveTrue(userId);
        if (settingOpt.isEmpty()) {
            return;
        }

        SavingsSetting setting = settingOpt.get();
        String keyword = setting.getKeyword();

        log.info("자동저축 검사 시작 - userId: {}, accountNo: {}, 미처리: {}", userId, primaryAccount.getAccountNo(), transactions.size());

        for (AccountTransaction t : transactions) {


            if ("1".equals(t.getTransactionType())
                    && ((t.getTransactionSummary() != null
                                    && t.getTransactionSummary().contains(keyword))
                            || (t.getTransactionMemo() != null
                                    && t.getTransactionMemo().contains(keyword)))) {

                log.info("자동저축 조건 일치 - transactionUniqueNo: {}", t.getTransactionUniqueNo());
                boolean success = executeSavingsTransfer(userId, setting);
                if (success) {
                    t.markAutoSavingsProcessed();
                }
            } else {
                t.markAutoSavingsProcessed();
            }
        }
    }

    private boolean executeSavingsTransfer(Long userId, SavingsSetting setting) {
        Account primaryAccount =
                accountRepository.findById(setting.getPrimaryAccountId()).orElse(null);
        Account saveboxAccount =
                accountRepository.findById(setting.getSaveboxAccountId()).orElse(null);

        if (primaryAccount == null || saveboxAccount == null) {
            log.warn("자동저축 중단 - 주계좌 또는 세이브박스 계좌를 찾을 수 없습니다. userId={}", userId);
            return false;
        }

        User user = userRepository.findById(userId).orElse(null);
        if (user == null) {
            log.warn("자동저축 중단 - 사용자를 찾을 수 없습니다. userId={}", userId);
            return false;
        }

        OpenBankTransferResponse apiResponse =
                openBankAdapter.fetchAccountTransfer(
                        user.getSsafyFinanceUserKey(),
                        saveboxAccount.getAccountNo(),
                        "(자동저축) 입금",
                        setting.getSavingsAmount().setScale(0, RoundingMode.DOWN).toString(),
                        primaryAccount.getAccountNo(),
                        "(자동저축) 출금");

        if (apiResponse == null || apiResponse.getHeader() == null) {
            log.error("자동 저축 이체 실패: API 응답이 비어 있습니다. userId={}", userId);
            return false;
        }

        String responseCode = apiResponse.getHeader().getResponseCode();
        if (!"H0000".equals(responseCode)) {
            log.error(
                    "자동 저축 이체 실패: userId={}, responseCode={}, message={}",
                    userId,
                    responseCode,
                    apiResponse.getHeader().getResponseMessage());
            return false;
        }

        log.info(
                "자동 저축 이체 성공 - userId={}, primaryAccountId={}, saveboxAccountId={}, amount={}",
                userId,
                primaryAccount.getId(),
                saveboxAccount.getId(),
                setting.getSavingsAmount());

        Account refreshedSavebox = saveboxAccount;

        try {
            syncAccounts(userId);

            refreshedSavebox =
                    accountRepository.findById(saveboxAccount.getId()).orElse(saveboxAccount);

            Integer cohortNo = user.getCohort() != null ? user.getCohort().getGenerationNo() : null;
            eventPublisher.publishEvent(
                    new SaveboxBalanceUpdatedEvent(
                            userId, refreshedSavebox.getBalance().longValue(), cohortNo));
        } catch (Exception e) {
            log.warn("자동저축 후 계좌 동기화/이벤트 발행 중 오류 - userId={}, message={}", userId, e.getMessage());
        }

        try {
            notificationService.createNotification(
                    userId,
                    NotificationType.AUTO_SAVINGS_COMPLETED,
                    "자동 저축이 완료되었어요",
                    String.format(
                            "%s 입금을 감지해 %s님의 세이브박스로 %s원이 자동 저축되었습니다.",
                            setting.getKeyword(),
                            resolveDisplayName(user.getNickname()),
                            formatAmount(setting.getSavingsAmount())),
                    NotificationReferenceType.FINANCE,
                    refreshedSavebox.getId());

            log.info(
                    "자동저축 알림 생성 완료 - userId={}, saveboxAccountId={}",
                    userId,
                    refreshedSavebox.getId());
        } catch (Exception e) {
            log.error("자동저축 알림 생성 실패 - userId={}, message={}", userId, e.getMessage(), e);
        }
        return true;
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


    @Transactional
    public void manualSavings(Long userId, BigDecimal amount, String password) {

        loginService.verifyPassword(userId, password);

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
            String msg = apiResponse.getHeader().getResponseMessage();
            if (msg != null && (msg.contains("잔액") || msg.contains("부족") || msg.contains("balance"))) {
                throw new AccountException(AccountErrorCode.INSUFFICIENT_BALANCE, msg);
            }
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR, msg);
        }

        syncAccounts(userId);

        notificationService.createNotification(
                userId,
                NotificationType.MANUAL_SAVINGS_COMPLETED,
                "저축이 완료되었어요",
                String.format(
                        "%s님의 세이브박스로 %s원이 저축되었습니다.",
                        resolveDisplayName(user.getNickname()), formatAmount(amount)),
                NotificationReferenceType.FINANCE,
                saveboxAccount.getId());
    }

    private void syncAccounts(Long userId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
        Optional<SavingsSetting> activeSettingOpt = savingsSettingRepository.findByUserIdAndIsActiveTrue(userId);

        String userKey = user.getSsafyFinanceUserKey();
        if (userKey == null || userKey.isBlank()) {
            return;
        }

        AccountListResponse listResponse = openBankAdapter.fetchDemandDepositAccounts(userKey);

        if (listResponse == null || listResponse.accounts() == null) {
            return;
        }

        for (AccountListResponse.AccountDetail detail : listResponse.accounts()) {
            String accountNo = detail.accountNo();
            Optional<Account> accountOpt = accountRepository.findByAccountNo(accountNo);

            BigDecimal balance = parseBigDecimal(detail.accountBalance());

            if (accountOpt.isPresent()) {
                Account existingAccount = accountOpt.get();
                BigDecimal oldBalance = existingAccount.getBalance();

                existingAccount.updateDynamicInfo(
                        detail.accountName(), balance, AccountStatus.ACTIVE);

                if (isRankingTargetAccount(existingAccount, activeSettingOpt)
                        && oldBalance.compareTo(balance) != 0) {
                    Integer cohortNo = user.getCohort() != null ? user.getCohort().getGenerationNo() : null;
                    eventPublisher.publishEvent(
                            new SaveboxBalanceUpdatedEvent(
                                    userId, balance.longValue(), cohortNo));
                }
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

                if (isRankingTargetAccount(newAccount, activeSettingOpt)) {
                    Integer cohortNo = user.getCohort() != null ? user.getCohort().getGenerationNo() : null;
                    eventPublisher.publishEvent(
                            new SaveboxBalanceUpdatedEvent(
                                    userId, balance.longValue(), cohortNo));
                }
            }
        }
    }

    private boolean isRankingTargetAccount(Account account, Optional<SavingsSetting> activeSettingOpt) {
        if (account.getAccountRole() == AccountRole.SAVE_BOX) {
            return true;
        }

        return activeSettingOpt
                .map(SavingsSetting::getSaveboxAccountId)
                .map(saveboxAccountId -> saveboxAccountId.equals(account.getId()))
                .orElse(false);
    }

    private String resolveDisplayName(String nickname) {
        if (nickname == null || nickname.isBlank()) {
            return "회원";
        }
        return nickname;
    }

    private String formatAmount(BigDecimal amount) {
        if (amount == null) {
            return "0";
        }
        return NumberFormat.getInstance().format(amount);
    }

    private LocalDate parseLocalDate(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) {
            return null;
        }

        String cleaned = dateStr.replaceAll("-", "");
        try {
            return LocalDate.parse(cleaned, DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            log.error("Failed to parse date: {}", dateStr);
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

    @Transactional
    public void manualWithdrawal(Long userId, BigDecimal amount, String password) {

        loginService.verifyPassword(userId, password);

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));

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


        BigDecimal transferAmount = amount.setScale(0, RoundingMode.DOWN);


        if (saveboxAccount.getBalance().compareTo(transferAmount) < 0) {
            throw new AccountException(AccountErrorCode.INSUFFICIENT_BALANCE);
        }

        OpenBankTransferResponse apiResponse =
                openBankAdapter.fetchAccountTransfer(
                        user.getSsafyFinanceUserKey(),
                        primaryAccount.getAccountNo(),
                        "(세이브박스) 꺼내기",
                        transferAmount.toString(),
                        saveboxAccount.getAccountNo(),
                        "(세이브박스) 출금");

        if (apiResponse == null || apiResponse.getHeader() == null) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }

        String responseCode = apiResponse.getHeader().getResponseCode();
        if (!"H0000".equals(responseCode)) {
            String msg = apiResponse.getHeader().getResponseMessage();
            if (msg != null && (msg.contains("잔액") || msg.contains("부족") || msg.contains("balance"))) {
                throw new AccountException(AccountErrorCode.INSUFFICIENT_BALANCE, msg);
            }
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR, msg);
        }

        syncAccounts(userId);

        notificationService.createNotification(
                userId,
                NotificationType.MANUAL_WITHDRAWAL_COMPLETED,
                "금고에서 돈을 꺼냈어요",
                String.format(
                        "세이브박스에서 %s원이 주계좌로 출금되었습니다.",
                        formatAmount(transferAmount)),
                NotificationReferenceType.FINANCE,
                saveboxAccount.getId());
    }
}
