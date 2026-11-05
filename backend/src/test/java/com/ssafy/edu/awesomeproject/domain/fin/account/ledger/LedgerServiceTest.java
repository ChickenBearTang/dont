package com.ssafy.edu.awesomeproject.domain.fin.account.ledger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeout;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.fin.FinFixtures;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import jakarta.persistence.EntityManager;
import java.math.BigDecimal;
import java.time.Duration;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.JdbcTemplate;

@DataJpaTest
@Import(LedgerService.class)
class LedgerServiceTest {

    @Autowired private LedgerService ledger;
    @Autowired private AccountRepository accounts;
    @Autowired private AccountTransactionRepository transactions;
    @Autowired private EntityManager em;
    @Autowired private JdbcTemplate jdbc;

    private User user;
    private Account primary;
    private Account savebox;

    @BeforeEach
    void setUp() {
        user = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 14), "ledger@test.dev");
        primary = ledger.openAccount(user, AccountRole.LINKED_DEPOSIT, null, true);
        savebox = ledger.openAccount(user, AccountRole.SAVE_BOX, null, false);
    }

    private static BigDecimal won(long amount) {
        return BigDecimal.valueOf(amount);
    }

    private BigDecimal balanceInDb(Long accountId) {
        em.flush();
        return jdbc.queryForObject("select balance from accounts where id = ?", BigDecimal.class, accountId);
    }

    @Test
    void opensAccountsWithZeroBalanceAndDistinctGeneratedNumbers() {
        Set<String> numbers = new HashSet<>();
        for (int i = 0; i < 30; i++) {
            Account account = ledger.openAccount(user, AccountRole.LINKED_DEPOSIT, "통장" + i, false);
            numbers.add(account.getAccountNo());
            assertThat(account.getBalance()).isEqualByComparingTo("0");
            assertThat(account.getAccountNo()).startsWith(LedgerService.BANK_CODE).hasSize(16);
        }
        assertThat(numbers).hasSize(30);
        assertThat(primary.getBankName()).isEqualTo(LedgerService.BANK_NAME);
        assertThat(primary.getAccountName()).isEqualTo("입출금 통장");
        assertThat(savebox.getAccountName()).isEqualTo("세이브박스");
        assertThat(savebox.getAccountTypeName()).isEqualTo("세이브박스");
        assertThat(primary.isPrimary()).isTrue();
    }

    @Test
    void depositIncreasesBalanceAndLeavesATransactionWithTheBalanceAfter() {
        AccountTransaction first = ledger.deposit(primary.getId(), won(2_600_000), "급여 입금", "DEMO", null);
        AccountTransaction second = ledger.deposit(primary.getId(), won(400_000), "용돈", null, null);

        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("3000000");
        assertThat(first.getTransactionType()).isEqualTo("1");
        assertThat(first.getAfterBalance()).isEqualByComparingTo("2600000");
        assertThat(second.getAfterBalance()).isEqualByComparingTo("3000000");
        assertThat(first.getTransactionUniqueNo()).isNotEqualTo(second.getTransactionUniqueNo());
        assertThat(first.isAutoSavingsProcessed()).isFalse();
    }

    @Test
    void transferMovesTheMoneyAndLeavesBothSidesWithTheCounterpartAccount() {
        ledger.deposit(primary.getId(), won(1_000_000), "급여 입금", null, null);

        LedgerService.TransferResult result =
                ledger.transfer(
                        primary.getId(),
                        savebox.getId(),
                        won(300_000),
                        LedgerSummaries.MANUAL_SAVINGS_OUT,
                        LedgerSummaries.MANUAL_SAVINGS_IN);

        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("700000");
        assertThat(balanceInDb(savebox.getId())).isEqualByComparingTo("300000");
        assertThat(result.amount()).isEqualByComparingTo("300000");

        List<AccountTransaction> out = transactions.findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(primary.getId());
        AccountTransaction withdrawal =
                out.stream().filter(t -> "2".equals(t.getTransactionType())).findFirst().orElseThrow();
        assertThat(withdrawal.getTransactionSummary()).isEqualTo(LedgerSummaries.MANUAL_SAVINGS_OUT);
        assertThat(withdrawal.getTransactionAccountNo()).isEqualTo(savebox.getAccountNo());
        assertThat(withdrawal.getAfterBalance()).isEqualByComparingTo("700000");

        AccountTransaction incoming =
                transactions.findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(savebox.getId()).get(0);
        assertThat(incoming.getTransactionType()).isEqualTo("1");
        assertThat(incoming.getTransactionSummary()).isEqualTo(LedgerSummaries.MANUAL_SAVINGS_IN);
        assertThat(incoming.getTransactionAccountNo()).isEqualTo(primary.getAccountNo());
        assertThat(incoming.getAfterBalance()).isEqualByComparingTo("300000");
    }

    @Test
    void insufficientBalanceChangesNothingAndLeavesNoTransactions() {
        ledger.deposit(primary.getId(), won(100_000), "입금", null, null);
        long before = transactions.count();

        assertThatThrownBy(
                        () ->
                                ledger.transfer(
                                        primary.getId(),
                                        savebox.getId(),
                                        won(100_001),
                                        LedgerSummaries.MANUAL_SAVINGS_OUT,
                                        LedgerSummaries.MANUAL_SAVINGS_IN))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.INSUFFICIENT_BALANCE));

        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("100000");
        assertThat(balanceInDb(savebox.getId())).isEqualByComparingTo("0");
        assertThat(transactions.count()).isEqualTo(before);
    }

    @Test
    void exactlyTheWholeBalanceCanBeTransferred() {
        ledger.deposit(primary.getId(), won(50_000), "입금", null, null);

        ledger.transfer(primary.getId(), savebox.getId(), won(50_000), "out", "in");

        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("0");
        assertThat(balanceInDb(savebox.getId())).isEqualByComparingTo("50000");
    }

    @Test
    void amountsMustBeWholePositiveWonAndAreNeverSilentlyRounded() {
        for (BigDecimal bad : new BigDecimal[] {null, BigDecimal.ZERO, won(-1), new BigDecimal("1000.5"), new BigDecimal("0.4")}) {
            assertThatThrownBy(() -> ledger.deposit(primary.getId(), bad, "x", null, null))
                    .as("deposit %s", bad)
                    .isInstanceOfSatisfying(
                            AccountException.class,
                            e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.INVALID_AMOUNT));
            assertThatThrownBy(() -> ledger.transfer(primary.getId(), savebox.getId(), bad, "o", "i"))
                    .as("transfer %s", bad)
                    .isInstanceOfSatisfying(
                            AccountException.class,
                            e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.INVALID_AMOUNT));
        }
        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("0");
        // 소수점이 0인 값(1000.00)은 정수 금액이다.
        ledger.deposit(primary.getId(), new BigDecimal("1000.00"), "입금", null, null);
        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("1000");
    }

    @Test
    void absurdMagnitudesAreRejectedQuicklyInsteadOfBeingExpanded() {
        // 지수 표기로 짧게 쓴 거대한 수. 예전에는 setScale 이 이걸 실제 정수로 펼치느라 CPU 를 쓰고(1E+4000000 은 약 2초)
        // 심지어 유효한 금액으로 통과시켰다. 크기를 먼저 보고 거절해야 한다.
        for (String huge :
                new String[] {"1E+4000000", "1E+999999999", "1E-4000000", "1E-999999999", "10000000000000"}) {
            BigDecimal amount = new BigDecimal(huge);
            assertTimeout(
                    Duration.ofSeconds(1),
                    () ->
                            assertThatThrownBy(() -> ledger.deposit(primary.getId(), amount, "x", null, null))
                                    .as("deposit %s", huge)
                                    .isInstanceOfSatisfying(
                                            AccountException.class,
                                            e ->
                                                    assertThat(e.getErrorCode())
                                                            .isEqualTo(AccountErrorCode.INVALID_AMOUNT)));
        }
        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("0");
        // 열(15자리, 소수 2자리)의 정수부 13자리 안에 드는 가장 큰 값은 받는다.
        ledger.deposit(primary.getId(), new BigDecimal("9999999999999"), "입금", null, null);
        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("9999999999999");
    }

    @Test
    void cannotTransferToTheSameAccountOrToAMissingOne() {
        ledger.deposit(primary.getId(), won(10_000), "입금", null, null);

        assertThatThrownBy(() -> ledger.transfer(primary.getId(), primary.getId(), won(1), "o", "i"))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.SAME_ACCOUNT_TRANSFER));
        assertThatThrownBy(() -> ledger.transfer(primary.getId(), 9_999_999L, won(1), "o", "i"))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.ACCOUNT_NOT_FOUND));
        assertThatThrownBy(() -> ledger.deposit(9_999_999L, won(1), "i", null, null))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.ACCOUNT_NOT_FOUND));
        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("10000");
    }

    @Test
    void oneTimeLimitIsEnforced() {
        ledger.deposit(primary.getId(), LedgerService.ONE_TIME_TRANSFER_LIMIT.add(won(1)), "큰 입금", null, null);

        assertThatThrownBy(
                        () ->
                                ledger.transfer(
                                        primary.getId(),
                                        savebox.getId(),
                                        LedgerService.ONE_TIME_TRANSFER_LIMIT.add(won(1)),
                                        "o",
                                        "i"))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.TRANSFER_LIMIT_EXCEEDED));
    }

    @Test
    void usesTheBalanceOtherTransactionsCommittedWhileWeWereWaitingForTheLock() {
        // 이 테스트의 핵심: 계좌를 먼저 읽어 둔 뒤(영속성 컨텍스트에 남은 값) 다른 트랜잭션이 잔액을 바꾼 상황.
        // 잠금 조회는 이미 읽은 엔티티를 덮어쓰지 않아서, 다시 읽지 않으면 오래된 잔액으로 계산해 돈이 사라지거나 생긴다.
        ledger.deposit(primary.getId(), won(100_000), "입금", null, null);
        em.flush();
        Account stale = accounts.findById(primary.getId()).orElseThrow();
        assertThat(stale.getBalance()).isEqualByComparingTo("100000");

        // 다른 트랜잭션이 커밋한 것처럼 DB 를 직접 바꾼다 (+900,000).
        jdbc.update("update accounts set balance = 1000000 where id = ?", primary.getId());

        ledger.transfer(primary.getId(), savebox.getId(), won(950_000), "o", "i");

        // 오래된 잔액(100,000)으로 계산했다면 잔액 부족으로 실패했을 이체다.
        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("50000");
        assertThat(balanceInDb(savebox.getId())).isEqualByComparingTo("950000");
    }

    @Test
    void aTransferAfterADepositInTheSameTransactionKeepsTheDeposit() {
        // 잠금 후 refresh 가 이 트랜잭션이 아직 flush 하지 않은 변경(입금)을 버리면 안 된다.
        ledger.deposit(primary.getId(), won(500_000), "급여 입금", null, null);
        ledger.transfer(primary.getId(), savebox.getId(), won(200_000), "o", "i");
        ledger.deposit(primary.getId(), won(1_000), "이자", null, null);

        assertThat(balanceInDb(primary.getId())).isEqualByComparingTo("301000");
        assertThat(balanceInDb(savebox.getId())).isEqualByComparingTo("200000");
    }

    @Test
    void balanceCanBeRecomputedFromTheTransactionHistory() {
        ledger.deposit(primary.getId(), won(2_000_000), "급여 입금", null, null);
        ledger.transfer(primary.getId(), savebox.getId(), won(300_000), "o", "i");
        ledger.transfer(savebox.getId(), primary.getId(), won(120_000), "o2", "i2");
        ledger.deposit(primary.getId(), won(5_000), "이자", null, null);
        em.flush();

        for (Account account : List.of(primary, savebox)) {
            BigDecimal replayed = BigDecimal.ZERO;
            List<AccountTransaction> history =
                    transactions.findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(account.getId());
            for (AccountTransaction tx : history) {
                replayed = replayed.add("1".equals(tx.getTransactionType()) ? tx.getTransactionAmount() : tx.getTransactionAmount().negate());
            }
            assertThat(replayed).isEqualByComparingTo(balanceInDb(account.getId()));
        }
        // 거래 후 잔액이 가장 마지막 거래와 일치한다.
        AccountTransaction latest = transactions.findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(primary.getId())
                .stream().max(java.util.Comparator.comparing(AccountTransaction::getId)).orElseThrow();
        assertThat(latest.getAfterBalance()).isEqualByComparingTo(balanceInDb(primary.getId()));
    }
}
