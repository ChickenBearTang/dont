package com.ssafy.edu.awesomeproject.domain.fin.profile.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.fin.FinFixtures;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountStatus;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import jakarta.persistence.EntityManager;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.JdbcTemplate;

@DataJpaTest
@Import(FinanceBudgetBasisService.class)
class FinanceBudgetBasisServiceTest {

    private static final LocalDate TODAY = LocalDate.of(2026, 11, 5);

    @Autowired private FinanceBudgetBasisService service;
    @Autowired private AccountRepository accounts;
    @Autowired private AccountTransactionRepository transactions;
    @Autowired private EntityManager em;
    @Autowired private JdbcTemplate jdbc;

    private User user;
    private Account primary;
    private Account savebox;

    @BeforeEach
    void setUp() {
        user = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 14), "basis@test.dev");
        primary = account(user, "9990000000000001", AccountRole.LINKED_DEPOSIT);
        savebox = account(user, "9990000000000002", AccountRole.SAVE_BOX);
    }

    private Account account(User owner, String number, AccountRole role) {
        return accounts.save(
                Account.builder()
                        .userId(owner.getId())
                        .accountNo(number)
                        .bankCode("999")
                        .bankName("DON'T 은행")
                        .accountRole(role)
                        .balance(BigDecimal.ZERO)
                        .status(AccountStatus.ACTIVE)
                        .build());
    }

    private void tx(Account account, LocalDate date, String type, long amount, String summary, String counterAccountNo) {
        transactions.save(
                AccountTransaction.builder()
                        .account(account)
                        .transactionUniqueNo("T" + System.nanoTime() + Math.abs(summary.hashCode()))
                        .transactionDate(date)
                        .transactionTime("090000")
                        .transactionType(type)
                        .transactionTypeName("1".equals(type) ? "입금" : "출금")
                        .transactionAccountNo(counterAccountNo)
                        .transactionAmount(BigDecimal.valueOf(amount))
                        .afterBalance(BigDecimal.ZERO)
                        .transactionSummary(summary)
                        .build());
    }

    private void aMonth(int month) {
        tx(primary, LocalDate.of(2026, month, 25), "1", 2_600_000, "급여 입금", null);
        tx(primary, LocalDate.of(2026, month, 1), "2", 500_000, "월세", null);
        tx(primary, LocalDate.of(2026, month, 15), "2", 50_000, "통신비", null);
        tx(primary, LocalDate.of(2026, month, 25), "2", 200_000, "(자동저축) 출금", savebox.getAccountNo());
        tx(savebox, LocalDate.of(2026, month, 25), "1", 200_000, "(자동저축) 입금", primary.getAccountNo());
    }

    @Test
    void estimatesIncomeAndFixedExpenseFromTheLastThreeFullMonths() {
        aMonth(8);
        aMonth(9);
        aMonth(10);
        tx(primary, LocalDate.of(2026, 11, 3), "1", 9_000_000, "이번 달 입금(관찰 구간 밖)", null);

        Optional<MonthlyBudgetBasisEstimator.Basis> basis = service.estimate(user.getId(), TODAY);

        assertThat(basis).isPresent();
        assertThat(basis.get().monthlyIncome()).isEqualTo(2_600_000);
        // 월세 + 통신비 + 매달 쌓는 비상금(자동저축)
        assertThat(basis.get().monthlyFixedExpense()).isEqualTo(750_000);
        assertThat(basis.get().observedMonths()).isEqualTo(3);
    }

    @Test
    void transfersBetweenMyOwnAccountsAreRecognisedByTheCounterpartAccountNumber() {
        aMonth(10);
        // 적요에는 아무 표시가 없어도 상대 계좌가 내 세이브박스면 소득이 아니고 소비도 아니다.
        tx(primary, LocalDate.of(2026, 10, 26), "1", 400_000, "이체", savebox.getAccountNo());
        tx(primary, LocalDate.of(2026, 10, 27), "2", 300_000, "이체", savebox.getAccountNo());

        MonthlyBudgetBasisEstimator.Basis basis = service.estimate(user.getId(), TODAY).orElseThrow();

        assertThat(basis.monthlyIncome()).isEqualTo(2_600_000);
        assertThat(basis.monthlyFixedExpense()).isEqualTo(750_000);
    }

    @Test
    void anotherUsersTransactionsAreNeverIncluded() {
        aMonth(10);
        User other = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 15), "basis2@test.dev");
        Account othersAccount = account(other, "9990000000000003", AccountRole.LINKED_DEPOSIT);
        tx(othersAccount, LocalDate.of(2026, 10, 25), "1", 50_000_000, "급여 입금", null);

        assertThat(service.estimate(user.getId(), TODAY).orElseThrow().monthlyIncome()).isEqualTo(2_600_000);
        assertThat(service.estimate(other.getId(), TODAY).orElseThrow().monthlyIncome()).isEqualTo(50_000_000);
    }

    @Test
    void noAccountsOrNoSalaryMeansNoEstimate() {
        User fresh = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 16), "basis3@test.dev");
        assertThat(service.estimate(fresh.getId(), TODAY)).isEmpty();

        tx(primary, LocalDate.of(2026, 10, 1), "2", 500_000, "월세", null);
        assertThat(service.estimate(user.getId(), TODAY)).isEmpty();
    }
}
