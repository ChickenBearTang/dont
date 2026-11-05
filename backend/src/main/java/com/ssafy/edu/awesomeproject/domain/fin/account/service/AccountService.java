package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.LoginService;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.AccountOpenRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.MockDepositRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.MockDepositResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.SavingsSettingResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.ledger.LedgerService;
import com.ssafy.edu.awesomeproject.domain.fin.account.ledger.LedgerSummaries;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import com.ssafy.edu.awesomeproject.domain.ranking.event.SaveboxBalanceUpdatedEvent;
import java.math.BigDecimal;
import java.text.NumberFormat;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 계좌, 세이브박스, 저축 규칙. 돈이 움직이는 일은 전부 {@link LedgerService}를 거친다 (외부 은행 API 없음).
 *
 * <p>한 요청이 여러 계좌를 건드리면 먼저 관련 계좌를 모두 id 순서로 잠근 뒤 움직인다. 같은 사용자의 자동저축과 수동
 * 저축, 꺼내기가 동시에 들어와도 서로 기다리기만 하고 교착하거나 같은 입금을 두 번 처리하지 않는다.
 */
@Slf4j
@Service
@Transactional
public class AccountService {

    private static final DateTimeFormatter BASIC_DATE = DateTimeFormatter.BASIC_ISO_DATE;
    private static final DateTimeFormatter ISO_DATE = DateTimeFormatter.ISO_LOCAL_DATE;

    private final LedgerService ledgerService;
    private final AccountRepository accountRepository;
    private final AccountTransactionRepository accountTransactionRepository;
    private final SavingsSettingRepository savingsSettingRepository;
    private final UserRepository userRepository;
    private final LoginService loginService;
    private final ApplicationEventPublisher eventPublisher;
    private final NotificationService notificationService;
    private final boolean mockDepositEnabled;

    public AccountService(
            LedgerService ledgerService,
            AccountRepository accountRepository,
            AccountTransactionRepository accountTransactionRepository,
            SavingsSettingRepository savingsSettingRepository,
            UserRepository userRepository,
            LoginService loginService,
            ApplicationEventPublisher eventPublisher,
            NotificationService notificationService,
            @Value("${finance.mock-data.enabled:false}") boolean mockDepositEnabled) {
        this.ledgerService = ledgerService;
        this.accountRepository = accountRepository;
        this.accountTransactionRepository = accountTransactionRepository;
        this.savingsSettingRepository = savingsSettingRepository;
        this.userRepository = userRepository;
        this.loginService = loginService;
        this.eventPublisher = eventPublisher;
        this.notificationService = notificationService;
        this.mockDepositEnabled = mockDepositEnabled;
    }

    // ------------------------------------------------------------------ 계좌 개설

    /** 입출금 계좌를 연다. 사용자의 첫 입출금 계좌는 주계좌가 된다. */
    public AccountCreateResponse openAccount(Long userId, AccountOpenRequest request) {
        User user = lockUser(userId);
        boolean first =
                accountRepository.findAllByUserId(userId).stream()
                        .noneMatch(a -> a.getAccountRole() == AccountRole.LINKED_DEPOSIT);
        Account account =
                ledgerService.openAccount(
                        user,
                        AccountRole.LINKED_DEPOSIT,
                        request == null ? null : request.accountName(),
                        first);
        log.info("입출금 계좌 개설 - userId={}, accountId={}, primary={}", userId, account.getId(), first);
        return toCreateResponse(account);
    }

    /** 세이브박스를 연다. 사용자당 하나다. */
    public AccountCreateResponse createSaveBox(Long userId, SaveBoxCreateRequest request) {
        User user = lockUser(userId);
        boolean exists =
                accountRepository.findAllByUserId(userId).stream()
                        .anyMatch(a -> a.getAccountRole() == AccountRole.SAVE_BOX);
        if (exists) {
            throw new AccountException(AccountErrorCode.SAVEBOX_ALREADY_EXISTS);
        }
        Account savebox =
                ledgerService.openAccount(
                        user,
                        AccountRole.SAVE_BOX,
                        request == null ? null : request.accountName(),
                        false);
        publishSaveboxBalance(user, savebox);
        log.info("세이브박스 개설 - userId={}, accountId={}", userId, savebox.getId());
        return toCreateResponse(savebox);
    }

    // ------------------------------------------------------------------ 조회

    @Transactional(readOnly = true)
    public AccountResponse getAccount(Long userId, Long accountId) {
        return AccountResponse.from(requireOwnedAccount(userId, accountId));
    }

    @Transactional(readOnly = true)
    public AccountListResponse getAccountList(Long userId) {
        return AccountListResponse.of(accountRepository.findAllByUserId(userId));
    }

    /**
     * 계좌 목록 새로고침. 외부에서 가져올 것이 없으므로 밀려 있던 자동저축(잔액이 모자라 미뤄진 건 등)을 처리하고
     * 목록을 다시 준다.
     */
    public AccountListResponse refreshAccountList(Long userId) {
        processPendingAutoSavings(userId);
        return getAccountList(userId);
    }

    @Transactional(readOnly = true)
    public AccountTransactionResponse getAccountTransactions(
            Long userId, Long accountId, String startDate, String endDate) {
        Account account = requireOwnedAccount(userId, accountId);

        LocalDate end = startOrEnd(endDate, LocalDate.now());
        LocalDate start = startOrEnd(startDate, end.minusMonths(3));
        if (start.isAfter(end)) {
            throw new AccountException(AccountErrorCode.INVALID_INPUT);
        }

        List<AccountTransaction> transactions =
                accountTransactionRepository
                        .findAllByAccountIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                accountId, start, end);

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
                                                                        .format(BASIC_DATE))
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

    public AccountResponse setPrimaryAccount(Long userId, Long accountId) {
        Account account = requireOwnedAccount(userId, accountId);
        for (Account other : accountRepository.findAllByUserId(userId)) {
            if (other.isPrimary()) {
                other.unsetPrimary();
            }
        }
        account.setAsPrimary();

        savingsSettingRepository
                .findByUserIdAndIsActiveTrue(userId)
                .ifPresent(setting -> setting.updatePrimaryAccount(accountId));

        return AccountResponse.from(account);
    }

    // ------------------------------------------------------------------ 저축 규칙

    public SavingsSettingResponse createOrUpdateSavingsSetting(
            Long userId, SavingsSettingRequest request) {
        requireOwnedAccount(userId, request.primaryAccountId());
        requireOwnedAccount(userId, request.saveboxAccountId());
        if (request.primaryAccountId().equals(request.saveboxAccountId())) {
            throw new AccountException(AccountErrorCode.SAME_ACCOUNT_TRANSFER);
        }

        SavingsSetting setting =
                savingsSettingRepository
                        .findByUserIdAndIsActiveTrue(userId)
                        .orElseGet(
                                () ->
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

        return toSettingResponse(savingsSettingRepository.save(setting));
    }

    @Transactional(readOnly = true)
    public SavingsSettingResponse getSavingsSetting(Long userId) {
        return savingsSettingRepository
                .findByUserIdAndIsActiveTrue(userId)
                .map(AccountService::toSettingResponse)
                .orElse(null);
    }

    // ------------------------------------------------------------------ 수동 저축 / 꺼내기

    /** 주계좌에서 세이브박스로 직접 옮긴다. */
    public void manualSavings(Long userId, BigDecimal amount, String password) {
        loginService.verifyPassword(userId, password);
        User user = findUser(userId);
        SavingsSetting setting = requireActiveSetting(userId);
        Account primary = requireOwned(userId, setting.getPrimaryAccountId(), AccountErrorCode.PRIMARY_ACCOUNT_NOT_FOUND);
        Account savebox = requireOwned(userId, setting.getSaveboxAccountId(), AccountErrorCode.SAVEBOX_ACCOUNT_NOT_FOUND);

        LedgerService.TransferResult result =
                ledgerService.transfer(
                        primary.getId(),
                        savebox.getId(),
                        amount,
                        LedgerSummaries.MANUAL_SAVINGS_OUT,
                        LedgerSummaries.MANUAL_SAVINGS_IN);
        publishSaveboxBalance(user, result.to());

        notificationService.createNotification(
                userId,
                NotificationType.MANUAL_SAVINGS_COMPLETED,
                "저축이 완료되었어요",
                String.format(
                        "%s님의 세이브박스로 %s원이 저축되었습니다.",
                        displayName(user.getNickname()), formatAmount(result.amount())),
                NotificationReferenceType.FINANCE,
                savebox.getId());
    }

    /** 세이브박스에서 주계좌로 직접 꺼낸다. */
    public void manualWithdrawal(Long userId, BigDecimal amount, String password) {
        loginService.verifyPassword(userId, password);
        User user = findUser(userId);
        SavingsSetting setting = requireActiveSetting(userId);
        Account primary = requireOwned(userId, setting.getPrimaryAccountId(), AccountErrorCode.PRIMARY_ACCOUNT_NOT_FOUND);
        Account savebox = requireOwned(userId, setting.getSaveboxAccountId(), AccountErrorCode.SAVEBOX_ACCOUNT_NOT_FOUND);

        LedgerService.TransferResult result =
                ledgerService.transfer(
                        savebox.getId(),
                        primary.getId(),
                        amount,
                        LedgerSummaries.SAVEBOX_WITHDRAW_OUT,
                        LedgerSummaries.SAVEBOX_WITHDRAW_IN);
        publishSaveboxBalance(user, result.from());

        notificationService.createNotification(
                userId,
                NotificationType.MANUAL_WITHDRAWAL_COMPLETED,
                "금고에서 돈을 꺼냈어요",
                String.format("세이브박스에서 %s원이 주계좌로 출금되었습니다.", formatAmount(result.amount())),
                NotificationReferenceType.FINANCE,
                savebox.getId());
    }

    // ------------------------------------------------------------------ 모의 입금 + 자동저축

    /**
     * 개발·시연용 입금. 외부 은행이 없어서 돈이 들어오는 경로가 이것뿐이다. 설정으로 켠 환경에서만 동작한다
     * (finance.mock-data.enabled=true).
     */
    public MockDepositResponse mockDeposit(Long userId, Long accountId, MockDepositRequest request) {
        if (!mockDepositEnabled) {
            throw new AccountException(AccountErrorCode.MOCK_DATA_DISABLED);
        }
        Account account = requireOwnedAccount(userId, accountId);
        if (account.getAccountRole() != AccountRole.LINKED_DEPOSIT) {
            throw new AccountException(AccountErrorCode.NOT_A_DEPOSIT_ACCOUNT);
        }

        Optional<SavingsSetting> setting = savingsSettingRepository.findByUserIdAndIsActiveTrue(userId);
        lockAll(accountId, setting);

        String summary =
                request.summary() == null || request.summary().isBlank() ? "입금" : request.summary().strip();
        AccountTransaction deposit =
                ledgerService.deposit(accountId, request.amount(), summary, request.memo(), null);

        BigDecimal saved = BigDecimal.ZERO;
        if (setting.isPresent()) {
            saved = processAutoSavings(userId, setting.get());
        }
        Account refreshed = accountRepository.findById(accountId).orElse(account);
        return MockDepositResponse.builder()
                .transactionUniqueNo(deposit.getTransactionUniqueNo())
                .balanceAfter(refreshed.getBalance())
                .autoSavingsExecuted(saved.signum() > 0)
                .autoSavingsAmount(saved)
                .build();
    }

    /** 자동저축 검사를 아직 안 받은 입금을 처리한다. 스케줄러와 계좌 새로고침이 쓴다. */
    public void processPendingAutoSavings(Long userId) {
        Optional<SavingsSetting> setting = savingsSettingRepository.findByUserIdAndIsActiveTrue(userId);
        if (setting.isEmpty()) {
            return;
        }
        lockAll(setting.get().getPrimaryAccountId(), setting);
        processAutoSavings(userId, setting.get());
    }

    /**
     * 주계좌의 미처리 입금 중 키워드가 맞는 것마다 세이브박스로 정해진 금액을 옮긴다. 호출하기 전에 관련 계좌를
     * 잠가 둬야 한다.
     *
     * <p>잔액이 모자라면 그 입금은 미처리로 남기고(다음 새로고침/스케줄에서 다시 시도) 뒤의 입금도 건드리지
     * 않는다. 입금 순서대로 처리해야 어느 입금에 대한 저축인지가 어긋나지 않는다.
     *
     * @return 이번에 자동저축으로 옮긴 총액
     */
    private BigDecimal processAutoSavings(Long userId, SavingsSetting setting) {
        Account primary = accountRepository.findById(setting.getPrimaryAccountId()).orElse(null);
        Account savebox = accountRepository.findById(setting.getSaveboxAccountId()).orElse(null);
        if (primary == null
                || savebox == null
                || !userId.equals(primary.getUserId())
                || !userId.equals(savebox.getUserId())) {
            log.warn("자동저축 중단 - 주계좌 또는 세이브박스를 찾을 수 없습니다. userId={}", userId);
            return BigDecimal.ZERO;
        }
        // 잠근 뒤에 다시 읽는다. 기다리는 동안 다른 요청이 이미 처리했을 수 있다.
        List<AccountTransaction> pending =
                accountTransactionRepository
                        .findAllByAccountIdAndAutoSavingsProcessedFalseOrderByIdAsc(primary.getId());
        if (pending.isEmpty()) {
            return BigDecimal.ZERO;
        }

        User user = findUser(userId);
        BigDecimal total = BigDecimal.ZERO;
        for (AccountTransaction tx : pending) {
            if (!matchesKeyword(tx, setting.getKeyword())) {
                tx.markAutoSavingsProcessed();
                continue;
            }
            BigDecimal amount = setting.getSavingsAmount();
            if (amount == null || amount.signum() <= 0) {
                tx.markAutoSavingsProcessed(); // 저축액을 0원으로 둔 규칙: 옮길 게 없다
                continue;
            }
            if (primary.getBalance().compareTo(amount) < 0) {
                log.warn(
                        "자동저축 보류 - 잔액 부족. userId={}, 잔액={}, 저축액={}",
                        userId,
                        primary.getBalance(),
                        amount);
                break;
            }
            LedgerService.TransferResult result =
                    ledgerService.transfer(
                            primary.getId(),
                            savebox.getId(),
                            amount,
                            LedgerSummaries.AUTO_SAVINGS_OUT,
                            LedgerSummaries.AUTO_SAVINGS_IN);
            tx.markAutoSavingsProcessed();
            total = total.add(result.amount());

            notificationService.createNotification(
                    userId,
                    NotificationType.AUTO_SAVINGS_COMPLETED,
                    "자동 저축이 완료되었어요",
                    String.format(
                            "%s 입금을 감지해 %s님의 세이브박스로 %s원이 자동 저축되었습니다.",
                            setting.getKeyword(),
                            displayName(user.getNickname()),
                            formatAmount(result.amount())),
                    NotificationReferenceType.FINANCE,
                    savebox.getId());
        }
        if (total.signum() > 0) {
            publishSaveboxBalance(user, savebox);
        }
        return total;
    }

    private static boolean matchesKeyword(AccountTransaction tx, String keyword) {
        if (!"1".equals(tx.getTransactionType()) || keyword == null || keyword.isBlank()) {
            return false;
        }
        // 이체로 들어온 돈(자동저축/꺼내기)은 입금이어도 급여가 아니다.
        if (LedgerSummaries.isInternal(tx.getTransactionSummary())) {
            return false;
        }
        return (tx.getTransactionSummary() != null && tx.getTransactionSummary().contains(keyword))
                || (tx.getTransactionMemo() != null && tx.getTransactionMemo().contains(keyword));
    }

    // ------------------------------------------------------------------ 내부 도우미

    private void lockAll(Long accountId, Optional<SavingsSetting> setting) {
        List<Long> ids = new ArrayList<>();
        ids.add(accountId);
        setting.ifPresent(
                s -> {
                    ids.add(s.getPrimaryAccountId());
                    ids.add(s.getSaveboxAccountId());
                });
        ledgerService.lockInOrder(ids);
    }

    private User findUser(Long userId) {
        return userRepository
                .findById(userId)
                .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
    }

    private User lockUser(Long userId) {
        return userRepository
                .findByIdForUpdate(userId)
                .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
    }

    private Account requireOwnedAccount(Long userId, Long accountId) {
        return requireOwned(userId, accountId, AccountErrorCode.ACCOUNT_NOT_FOUND);
    }

    private Account requireOwned(Long userId, Long accountId, AccountErrorCode notFound) {
        if (accountId == null) {
            throw new AccountException(notFound);
        }
        return accountRepository
                .findById(accountId)
                .filter(account -> account.getUserId().equals(userId))
                .orElseThrow(() -> new AccountException(notFound));
    }

    private SavingsSetting requireActiveSetting(Long userId) {
        return savingsSettingRepository
                .findByUserIdAndIsActiveTrue(userId)
                .orElseThrow(() -> new AccountException(AccountErrorCode.SAVINGS_SETTING_NOT_FOUND));
    }

    private void publishSaveboxBalance(User user, Account savebox) {
        Integer cohortNo = user.getCohort() != null ? user.getCohort().getGenerationNo() : null;
        eventPublisher.publishEvent(
                new SaveboxBalanceUpdatedEvent(
                        user.getId(), savebox.getBalance().longValue(), cohortNo));
    }

    private static AccountCreateResponse toCreateResponse(Account account) {
        return AccountCreateResponse.builder()
                .accountNo(account.getAccountNo())
                .bankCode(account.getBankCode())
                .bankName(account.getBankName())
                .build();
    }

    private static SavingsSettingResponse toSettingResponse(SavingsSetting saved) {
        return SavingsSettingResponse.builder()
                .id(saved.getId())
                .primaryAccountId(saved.getPrimaryAccountId())
                .saveboxAccountId(saved.getSaveboxAccountId())
                .keyword(saved.getKeyword())
                .savingsAmount(saved.getSavingsAmount())
                .isActive(saved.isActive())
                .build();
    }

    /** yyyyMMdd 또는 yyyy-MM-dd. 비어 있으면 기본값, 형식이 틀리면 400 (조용히 무시하지 않는다). */
    private static LocalDate startOrEnd(String raw, LocalDate fallback) {
        if (raw == null || raw.isBlank()) {
            return fallback;
        }
        String value = raw.strip();
        try {
            return value.contains("-") ? LocalDate.parse(value, ISO_DATE) : LocalDate.parse(value, BASIC_DATE);
        } catch (DateTimeParseException exception) {
            throw new AccountException(AccountErrorCode.INVALID_INPUT);
        }
    }

    private static String displayName(String nickname) {
        return nickname == null || nickname.isBlank() ? "회원" : nickname;
    }

    private static String formatAmount(BigDecimal amount) {
        return amount == null ? "0" : NumberFormat.getInstance(Locale.KOREA).format(amount);
    }
}
