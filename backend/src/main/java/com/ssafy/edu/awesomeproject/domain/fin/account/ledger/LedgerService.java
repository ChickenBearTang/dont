package com.ssafy.edu.awesomeproject.domain.fin.account.ledger;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountStatus;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import jakarta.persistence.EntityManager;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/**
 * 서비스 안에서 도는 계좌 원장.
 *
 * <p>외부 은행 API 없이 계좌 개설, 입금, 이체를 처리한다. 잔액을 바꾸는 모든 경로는 이 클래스를 거친다.
 *
 * <ul>
 *   <li>잔액이 바뀌는 계좌는 행 잠금(SELECT ... FOR UPDATE)을 잡고 바꾼다. 여러 계좌는 항상 id 오름차순으로
 *       잠가서 서로 반대 방향 이체가 교착하지 않는다.
 *   <li>한 번의 이체는 출금 거래와 입금 거래를 같은 트랜잭션에 남긴다. 잔액 부족이면 아무것도 남지 않는다.
 *   <li>거래마다 거래 후 잔액(afterBalance)을 남기므로 거래 내역만으로 잔액을 다시 계산해 검증할 수 있다.
 * </ul>
 *
 * <p>트랜잭션은 호출하는 쪽에서 열어 둔 것을 쓴다 (MANDATORY). 그래서 여러 원장 동작과 알림, 랭킹 이벤트를
 * 하나의 작업 단위로 묶을 수 있다. 검증(금액, 잔액, 한도)은 잔액을 바꾸기 전에 모두 끝나므로, 호출하는 쪽이
 * AccountException 을 잡고 다음 일을 계속해도 되도록 AccountException 은 롤백 대상에서 뺐다 (noRollbackFor).
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class LedgerService {

    public static final String BANK_CODE = "999";
    public static final String BANK_NAME = "DON'T 은행";
    public static final String CURRENCY = "KRW";
    static final String ACCOUNT_TYPE_CODE_DEMAND = "1";
    static final String ACCOUNT_TYPE_NAME_DEMAND = "수시입출금";
    static final String ACCOUNT_TYPE_CODE_SAVEBOX = "2";
    static final String ACCOUNT_TYPE_NAME_SAVEBOX = "세이브박스";

    /** 한 번에 이체할 수 있는 금액과 하루 한도. 입출금 모의 계좌의 안전장치다. */
    public static final BigDecimal ONE_TIME_TRANSFER_LIMIT = new BigDecimal("100000000");

    public static final BigDecimal DAILY_TRANSFER_LIMIT = new BigDecimal("500000000");

    /**
     * 한 건의 금액 정수부 최대 자릿수. 잔액·거래 금액 열이 numeric(15, 2) 라서 정수부는 13자리까지다
     * (DTO 의 @Digits 와 같은 값).
     */
    public static final int MAX_AMOUNT_DIGITS = 13;

    static final String TYPE_DEPOSIT = "1";
    static final String TYPE_WITHDRAWAL = "2";
    private static final int ACCOUNT_NO_RETRIES = 20;
    private static final DateTimeFormatter TX_STAMP = DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS");
    private static final DateTimeFormatter TX_TIME = DateTimeFormatter.ofPattern("HHmmss");

    private final AccountRepository accountRepository;
    private final AccountTransactionRepository accountTransactionRepository;
    private final EntityManager entityManager;

    /** 이체 한 건의 결과. 호출하는 쪽이 알림·이벤트에 쓴다. */
    public record TransferResult(Account from, Account to, BigDecimal amount) {}

    /** 새 계좌를 연다. 잔액은 0원이다 (입금은 {@link #deposit}으로 한다). */
    @Transactional(propagation = Propagation.MANDATORY, noRollbackFor = AccountException.class)
    public Account openAccount(User user, AccountRole role, String accountName, boolean primary) {
        String number = nextAccountNo();
        LocalDate today = LocalDate.now();
        boolean savebox = role == AccountRole.SAVE_BOX;
        Account account =
                Account.builder()
                        .userId(user.getId())
                        .accountNo(number)
                        .bankCode(BANK_CODE)
                        .bankName(BANK_NAME)
                        .accountRole(role)
                        .isPrimary(primary)
                        .accountTypeCode(savebox ? ACCOUNT_TYPE_CODE_SAVEBOX : ACCOUNT_TYPE_CODE_DEMAND)
                        .accountTypeName(savebox ? ACCOUNT_TYPE_NAME_SAVEBOX : ACCOUNT_TYPE_NAME_DEMAND)
                        .accountName(blankToDefault(accountName, savebox ? "세이브박스" : "입출금 통장"))
                        .accountCreatedDate(today)
                        .accountExpiryDate(today.plusYears(5))
                        .dailyTransferLimit(DAILY_TRANSFER_LIMIT)
                        .oneTimeTransferLimit(ONE_TIME_TRANSFER_LIMIT)
                        .balance(BigDecimal.ZERO)
                        .lastTransactionDate(null)
                        .currencyCode(CURRENCY)
                        .status(AccountStatus.ACTIVE)
                        .userName(user.getName())
                        .build();
        return accountRepository.save(account);
    }

    /** 계좌에 돈이 들어온 거래를 남긴다. 반환한 거래는 아직 자동저축 검사를 받지 않은 상태다. */
    @Transactional(propagation = Propagation.MANDATORY, noRollbackFor = AccountException.class)
    public AccountTransaction deposit(
            Long accountId, BigDecimal amount, String summary, String memo, String counterAccountNo) {
        BigDecimal won = normalizeAmount(amount);
        Account account = lockInOrder(List.of(accountId)).get(accountId);
        if (account == null) {
            throw new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND);
        }
        return applyDeposit(account, won, "입금", summary, memo, counterAccountNo);
    }

    /**
     * 출금 계좌에서 입금 계좌로 이체한다. 두 계좌를 id 오름차순으로 잠근다.
     *
     * @throws AccountException 잔액이 부족하거나 금액·계좌가 올바르지 않을 때. 이때 잔액과 거래는 그대로다.
     */
    @Transactional(propagation = Propagation.MANDATORY, noRollbackFor = AccountException.class)
    public TransferResult transfer(
            Long fromAccountId,
            Long toAccountId,
            BigDecimal amount,
            String fromSummary,
            String toSummary) {
        BigDecimal won = normalizeAmount(amount);
        if (fromAccountId == null || toAccountId == null || fromAccountId.equals(toAccountId)) {
            throw new AccountException(AccountErrorCode.SAME_ACCOUNT_TRANSFER);
        }
        Map<Long, Account> locked = lockInOrder(List.of(fromAccountId, toAccountId));
        Account from = locked.get(fromAccountId);
        Account to = locked.get(toAccountId);
        if (from == null || to == null) {
            throw new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND);
        }
        requireActive(from);
        requireActive(to);
        BigDecimal limit = from.getOneTimeTransferLimit();
        if (limit != null && won.compareTo(limit) > 0) {
            throw new AccountException(AccountErrorCode.TRANSFER_LIMIT_EXCEEDED);
        }
        if (from.getBalance().compareTo(won) < 0) {
            throw new AccountException(AccountErrorCode.INSUFFICIENT_BALANCE);
        }

        LocalDate today = LocalDate.now();
        String time = LocalDateTime.now().format(TX_TIME);
        from.applyWithdrawal(won, today);
        accountTransactionRepository.save(
                transaction(from, TYPE_WITHDRAWAL, "출금(이체)", won, fromSummary, null, to.getAccountNo(), time, today));
        to.applyDeposit(won, today);
        // 본인 계좌에서 온 돈은 급여가 아니라서 자동저축 검사 대상이 아니다. 처음부터 처리 끝난 것으로 남긴다.
        AccountTransaction incoming =
                transaction(to, TYPE_DEPOSIT, "입금(이체)", won, toSummary, null, from.getAccountNo(), time, today);
        incoming.markAutoSavingsProcessed();
        accountTransactionRepository.save(incoming);
        return new TransferResult(from, to, won);
    }

    /**
     * 여러 계좌를 id 오름차순으로 한꺼번에 잠그고 최신 상태로 읽는다. 한 작업이 계좌 여러 개를 건드릴 때는 건드리기
     * 전에 이걸로 먼저 모두 잠가야 한다 (이미 잠근 행을 다시 잠그는 건 같은 트랜잭션에서는 문제없다).
     *
     * <p>잠그기 전에 이미 읽어 둔 계좌는 영속성 컨텍스트에 오래된 잔액으로 남아 있다. 잠금 조회는 그 값을 덮어쓰지
     * 않으므로, 잠근 뒤에 다시 읽어(refresh) 기다리는 동안 다른 요청이 커밋한 잔액을 받아 온다. refresh 가 이
     * 트랜잭션이 바꿔 둔 값을 버리지 않도록 먼저 flush 한다.
     */
    @Transactional(propagation = Propagation.MANDATORY, noRollbackFor = AccountException.class)
    public Map<Long, Account> lockInOrder(Collection<Long> accountIds) {
        TreeSet<Long> ordered = new TreeSet<>();
        for (Long id : accountIds) {
            if (id != null) {
                ordered.add(id);
            }
        }
        if (ordered.isEmpty()) {
            return Map.of();
        }
        entityManager.flush();
        List<Account> accounts =
                new ArrayList<>(accountRepository.findAllByIdInForUpdateOrderById(ordered));
        for (Account account : accounts) {
            entityManager.refresh(account);
        }
        return accounts.stream().collect(Collectors.toMap(Account::getId, Function.identity()));
    }

    private AccountTransaction applyDeposit(
            Account account,
            BigDecimal won,
            String typeName,
            String summary,
            String memo,
            String counterAccountNo) {
        requireActive(account);
        LocalDate today = LocalDate.now();
        account.applyDeposit(won, today);
        return accountTransactionRepository.save(
                transaction(
                        account,
                        TYPE_DEPOSIT,
                        typeName,
                        won,
                        summary,
                        memo,
                        counterAccountNo,
                        LocalDateTime.now().format(TX_TIME),
                        today));
    }

    /** 출금 행은 자동저축 검사 대상이 아니라서 처음부터 처리 끝난 것으로 만든다. 입금 행만 검사 대기로 시작한다. */
    private AccountTransaction transaction(
            Account account,
            String type,
            String typeName,
            BigDecimal amount,
            String summary,
            String memo,
            String counterAccountNo,
            String time,
            LocalDate date) {
        AccountTransaction transaction =
                AccountTransaction.builder()
                .account(account)
                .transactionUniqueNo(nextTransactionNo())
                .transactionDate(date)
                .transactionTime(time)
                .transactionType(type)
                .transactionTypeName(typeName)
                .transactionAccountNo(counterAccountNo)
                .transactionAmount(amount)
                .afterBalance(account.getBalance())
                .transactionSummary(summary)
                .transactionMemo(memo)
                .build();
        if (TYPE_WITHDRAWAL.equals(type)) {
            transaction.markAutoSavingsProcessed();
        }
        return transaction;
    }

    private static void requireActive(Account account) {
        if (account.getStatus() != AccountStatus.ACTIVE) {
            throw new AccountException(AccountErrorCode.ACCOUNT_NOT_ACTIVE);
        }
    }

    /**
     * 원 단위 정수만 받는다. 0 이하이거나 소수점 이하가 남는 금액은 거절한다 (조용히 내림하지 않는다).
     *
     * <p>금액은 요청 본문에서 그대로 온다. "1E+4000000" 처럼 짧은 지수 표기는 BigDecimal 로는 아주 작지만 setScale 로
     * 정수로 펼치면 400만 자리가 되어 CPU 를 쓰고(약 2초) 열 범위를 넘는 채로 DB 까지 간다. 그래서 펼치기 전에 크기를
     * 먼저 본다 (stripTrailingZeros 는 지수만 만지므로 값이 커도 싸다).
     */
    static BigDecimal normalizeAmount(BigDecimal amount) {
        if (amount == null || amount.signum() <= 0) {
            throw new AccountException(AccountErrorCode.INVALID_AMOUNT);
        }
        BigDecimal stripped = amount.stripTrailingZeros();
        if (stripped.scale() > 0) { // 소수점 이하가 남는다 (1E-4000000 도 여기서 걸린다)
            throw new AccountException(AccountErrorCode.INVALID_AMOUNT);
        }
        if (stripped.precision() - stripped.scale() > MAX_AMOUNT_DIGITS) { // 열에 안 들어가는 크기
            throw new AccountException(AccountErrorCode.INVALID_AMOUNT);
        }
        return stripped.setScale(0); // scale <= 0 이고 자릿수가 제한돼 있어 정확하고 싸다
    }

    private String nextAccountNo() {
        for (int attempt = 0; attempt < ACCOUNT_NO_RETRIES; attempt++) {
            StringBuilder digits = new StringBuilder(BANK_CODE);
            for (int i = 0; i < 13; i++) {
                digits.append(ThreadLocalRandom.current().nextInt(10));
            }
            String candidate = digits.toString();
            if (!accountRepository.existsByAccountNo(candidate)) {
                return candidate;
            }
        }
        // 계좌번호가 거의 다 찼다는 뜻이다. 만들어 내지 않고 실패시킨다.
        throw new AccountException(AccountErrorCode.ACCOUNT_NO_EXHAUSTED);
    }

    private static String nextTransactionNo() {
        String random = UUID.randomUUID().toString().replace("-", "").substring(0, 8);
        return "T" + LocalDateTime.now().format(TX_STAMP) + random;
    }

    private static String blankToDefault(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value.strip();
    }
}
