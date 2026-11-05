package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthErrorCode;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.service.LoginService;
import com.ssafy.edu.awesomeproject.domain.fin.FinFixtures;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.AccountOpenRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.MockDepositRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.MockDepositResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.ledger.LedgerService;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import com.ssafy.edu.awesomeproject.domain.ranking.event.SaveboxBalanceUpdatedEvent;
import jakarta.persistence.EntityManager;
import java.math.BigDecimal;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.event.ApplicationEvents;
import org.springframework.test.context.event.RecordApplicationEvents;

/** 계좌 개설 → 입금 → 자동저축/수동저축/꺼내기 흐름을 실제 DB(H2)로 검증한다. 외부 호출이 없다. */
@DataJpaTest
@Import({AccountService.class, LedgerService.class})
@RecordApplicationEvents
class AccountServiceFlowTest {

    @Autowired private AccountService service;
    @Autowired private LedgerService ledger;
    @Autowired private AccountRepository accounts;
    @Autowired private AccountTransactionRepository transactions;
    @Autowired private SavingsSettingRepository settings;
    @Autowired private UserRepository users;
    @Autowired private ApplicationEventPublisher publisher;
    @Autowired private EntityManager em;
    @Autowired private JdbcTemplate jdbc;
    @Autowired private ApplicationEvents events;

    @MockitoBean private LoginService loginService;
    @MockitoBean private NotificationService notifications;

    private User user;
    private Long primaryId;
    private Long saveboxId;

    @BeforeEach
    void setUp() {
        user = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 14), "flow@test.dev");
        AccountCreateResponse primary = service.openAccount(user.getId(), new AccountOpenRequest("월급통장"));
        AccountCreateResponse savebox = service.createSaveBox(user.getId(), null);
        primaryId = accounts.findByAccountNo(primary.accountNo()).orElseThrow().getId();
        saveboxId = accounts.findByAccountNo(savebox.accountNo()).orElseThrow().getId();
    }

    private void saveRule(String keyword, long amount) {
        service.createOrUpdateSavingsSetting(
                user.getId(),
                SavingsSettingRequest.builder()
                        .primaryAccountId(primaryId)
                        .saveboxAccountId(saveboxId)
                        .keyword(keyword)
                        .savingsAmount(BigDecimal.valueOf(amount))
                        .isActive(true)
                        .build());
    }

    private MockDepositResponse deposit(String summary, long amount) {
        return service.mockDeposit(
                user.getId(), primaryId, new MockDepositRequest(BigDecimal.valueOf(amount), summary, null));
    }

    private BigDecimal balance(Long accountId) {
        em.flush();
        return jdbc.queryForObject("select balance from accounts where id = ?", BigDecimal.class, accountId);
    }

    private long processedFlagCount(boolean processed) {
        em.flush();
        return jdbc.queryForObject(
                "select count(*) from account_transactions where account_id = ? and auto_savings_processed = ?",
                Long.class,
                primaryId,
                processed);
    }

    // ------------------------------------------------------------ 계좌 개설

    @Test
    void firstDemandAccountBecomesPrimaryAndTheSecondDoesNot() {
        service.openAccount(user.getId(), null);

        List<AccountListResponse.AccountDetail> list = service.getAccountList(user.getId()).accounts();
        assertThat(list).hasSize(3);
        assertThat(list.stream().filter(a -> Boolean.TRUE.equals(a.isPrimary()))).hasSize(1);
        assertThat(accounts.findById(primaryId).orElseThrow().isPrimary()).isTrue();
    }

    @Test
    void aUserGetsOnlyOneSavebox() {
        assertThatThrownBy(() -> service.createSaveBox(user.getId(), new SaveBoxCreateRequest("두 번째")))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.SAVEBOX_ALREADY_EXISTS));
    }

    @Test
    void creatingTheSaveboxPublishesARankingEvent() {
        assertThat(events.stream(SaveboxBalanceUpdatedEvent.class))
                .anySatisfy(
                        e -> {
                            assertThat(e.userId()).isEqualTo(user.getId());
                            assertThat(e.currentBalance()).isZero();
                            assertThat(e.cohort()).isEqualTo(14);
                        });
    }

    // ------------------------------------------------------------ 모의 입금 + 자동저축

    @Test
    void salaryDepositWithTheKeywordTriggersAutoSavingsImmediately() {
        saveRule("삼성SSAFY", 100_000);

        MockDepositResponse response = deposit("삼성SSAFY 급여", 2_600_000);

        assertThat(response.autoSavingsExecuted()).isTrue();
        assertThat(response.autoSavingsAmount()).isEqualByComparingTo("100000");
        assertThat(response.balanceAfter()).isEqualByComparingTo("2500000");
        assertThat(balance(primaryId)).isEqualByComparingTo("2500000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("100000");
        assertThat(processedFlagCount(false)).as("처리 안 된 입금이 남지 않는다").isZero();

        AccountTransactionResponse savebox = service.getAccountTransactions(user.getId(), saveboxId, null, null);
        assertThat(savebox.transactions()).hasSize(1);
        assertThat(savebox.transactions().get(0).transactionSummary()).isEqualTo("(자동저축) 입금");
        AccountTransactionResponse main = service.getAccountTransactions(user.getId(), primaryId, null, null);
        assertThat(main.transactions())
                .extracting(AccountTransactionResponse.TransactionItem::transactionSummary)
                .containsExactlyInAnyOrder("삼성SSAFY 급여", "(자동저축) 출금");

        verify(notifications)
                .createNotification(
                        eq(user.getId()),
                        eq(NotificationType.AUTO_SAVINGS_COMPLETED),
                        anyString(),
                        anyString(),
                        eq(NotificationReferenceType.FINANCE),
                        eq(saveboxId));
        assertThat(events.stream(SaveboxBalanceUpdatedEvent.class).map(SaveboxBalanceUpdatedEvent::currentBalance))
                .contains(100_000L);
    }

    @Test
    void aDepositWithoutTheKeywordIsMarkedProcessedAndNothingMoves() {
        saveRule("삼성SSAFY", 100_000);

        MockDepositResponse response = deposit("용돈", 50_000);

        assertThat(response.autoSavingsExecuted()).isFalse();
        assertThat(balance(primaryId)).isEqualByComparingTo("50000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("0");
        assertThat(processedFlagCount(false)).isZero();
        verify(notifications, never()).createNotification(anyLong(), any(), anyString(), anyString(), any(), any());
    }

    @Test
    void moneyComingBackFromTheSaveboxIsNeverTreatedAsSalary() {
        // 키워드가 "세이브박스"이면 꺼내기로 들어온 "(세이브박스) 꺼내기" 입금이 키워드를 포함한다.
        // 본인 계좌에서 되돌아온 돈이 급여로 읽혀 다시 저축되면 안 된다.
        saveRule("세이브박스", 10_000);
        ledger.deposit(saveboxId, BigDecimal.valueOf(200_000), "(이월) 시작 잔액", null, null);
        service.manualWithdrawal(user.getId(), BigDecimal.valueOf(100_000), "pw");

        service.processPendingAutoSavings(user.getId());

        assertThat(balance(primaryId)).isEqualByComparingTo("100000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("100000");
        assertThat(processedFlagCount(false)).isZero();
    }

    @Test
    void autoSavingsIsDeferredWhenTheBalanceIsTooLowAndCaughtUpLater() {
        saveRule("급여", 300_000);

        MockDepositResponse first = deposit("급여", 100_000); // 잔액 10만 < 저축액 30만
        assertThat(first.autoSavingsExecuted()).isFalse();
        assertThat(processedFlagCount(false)).as("보류된 입금은 미처리로 남는다").isEqualTo(1);
        assertThat(balance(saveboxId)).isEqualByComparingTo("0");

        MockDepositResponse second = deposit("용돈", 500_000); // 잔액 60만 → 밀려 있던 급여 건이 처리된다

        assertThat(second.autoSavingsExecuted()).isTrue();
        assertThat(balance(primaryId)).isEqualByComparingTo("300000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("300000");
        assertThat(processedFlagCount(false)).isZero();
    }

    @Test
    void eachMatchingDepositSavesOnceEvenWhenProcessedRepeatedly() {
        saveRule("급여", 100_000);
        deposit("급여", 1_000_000);

        service.processPendingAutoSavings(user.getId());
        service.processPendingAutoSavings(user.getId());
        service.refreshAccountList(user.getId());

        assertThat(balance(saveboxId)).isEqualByComparingTo("100000");
        assertThat(balance(primaryId)).isEqualByComparingTo("900000");
    }

    @Test
    void mockDepositIsRefusedWhenTheFlagIsOffAndOnlyForDemandAccountsOfTheOwner() {
        AccountService off =
                new AccountService(ledger, accounts, transactions, settings, users, loginService, publisher, notifications, false);
        assertThatThrownBy(
                        () -> off.mockDeposit(user.getId(), primaryId, new MockDepositRequest(BigDecimal.TEN, null, null)))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.MOCK_DATA_DISABLED));

        assertThatThrownBy(() -> service.mockDeposit(user.getId(), saveboxId, new MockDepositRequest(BigDecimal.TEN, null, null)))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.NOT_A_DEPOSIT_ACCOUNT));

        User other = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 15), "other@test.dev");
        assertThatThrownBy(() -> service.mockDeposit(other.getId(), primaryId, new MockDepositRequest(BigDecimal.TEN, null, null)))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.ACCOUNT_NOT_FOUND));
    }

    // ------------------------------------------------------------ 수동 저축 / 꺼내기

    @Test
    void manualSavingsAndWithdrawalMoveMoneyBetweenPrimaryAndSavebox() {
        saveRule("급여", 100_000);
        deposit("용돈", 700_000);

        service.manualSavings(user.getId(), BigDecimal.valueOf(250_000), "pw");
        assertThat(balance(primaryId)).isEqualByComparingTo("450000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("250000");

        service.manualWithdrawal(user.getId(), BigDecimal.valueOf(50_000), "pw");
        assertThat(balance(primaryId)).isEqualByComparingTo("500000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("200000");

        verify(loginService, org.mockito.Mockito.times(2)).verifyPassword(eq(user.getId()), eq("pw"));
        verify(notifications).createNotification(eq(user.getId()), eq(NotificationType.MANUAL_SAVINGS_COMPLETED), anyString(), anyString(), any(), eq(saveboxId));
        verify(notifications).createNotification(eq(user.getId()), eq(NotificationType.MANUAL_WITHDRAWAL_COMPLETED), anyString(), anyString(), any(), eq(saveboxId));
    }

    @Test
    void manualSavingsAndWithdrawalRefuseWhenThereIsNotEnoughMoney() {
        saveRule("급여", 100_000);
        deposit("용돈", 10_000);

        assertThatThrownBy(() -> service.manualSavings(user.getId(), BigDecimal.valueOf(10_001), "pw"))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.INSUFFICIENT_BALANCE));
        assertThatThrownBy(() -> service.manualWithdrawal(user.getId(), BigDecimal.valueOf(1), "pw"))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.INSUFFICIENT_BALANCE));

        assertThat(balance(primaryId)).isEqualByComparingTo("10000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("0");
        verify(notifications, never()).createNotification(anyLong(), eq(NotificationType.MANUAL_SAVINGS_COMPLETED), anyString(), anyString(), any(), any());
    }

    @Test
    void aWrongPasswordMovesNothing() {
        saveRule("급여", 100_000);
        deposit("용돈", 500_000);
        doThrow(new AuthException(AuthErrorCode.BAD_CREDENTIALS)).when(loginService).verifyPassword(anyLong(), eq("틀림"));

        assertThatThrownBy(() -> service.manualSavings(user.getId(), BigDecimal.valueOf(1_000), "틀림"))
                .isInstanceOf(AuthException.class);

        assertThat(balance(primaryId)).isEqualByComparingTo("500000");
        assertThat(balance(saveboxId)).isEqualByComparingTo("0");
    }

    @Test
    void manualSavingsNeedsAnActiveRule() {
        assertThatThrownBy(() -> service.manualSavings(user.getId(), BigDecimal.valueOf(1_000), "pw"))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.SAVINGS_SETTING_NOT_FOUND));
    }

    // ------------------------------------------------------------ 저축 규칙 / 접근 제어 / 입력 검증

    @Test
    void aRuleMustUseTwoDifferentAccountsOwnedByTheUser() {
        assertThatThrownBy(
                        () ->
                                service.createOrUpdateSavingsSetting(
                                        user.getId(),
                                        SavingsSettingRequest.builder()
                                                .primaryAccountId(primaryId)
                                                .saveboxAccountId(primaryId)
                                                .keyword("급여")
                                                .savingsAmount(BigDecimal.TEN)
                                                .isActive(true)
                                                .build()))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.SAME_ACCOUNT_TRANSFER));

        User other = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 15), "other2@test.dev");
        Long othersAccount = accounts.save(Account.builder().userId(other.getId()).accountNo("9990000000000001")
                .bankCode("999").bankName("x").accountRole(AccountRole.LINKED_DEPOSIT).balance(BigDecimal.ZERO)
                .status(com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountStatus.ACTIVE).build()).getId();
        assertThatThrownBy(
                        () ->
                                service.createOrUpdateSavingsSetting(
                                        user.getId(),
                                        SavingsSettingRequest.builder()
                                                .primaryAccountId(othersAccount)
                                                .saveboxAccountId(saveboxId)
                                                .keyword("급여")
                                                .savingsAmount(BigDecimal.TEN)
                                                .isActive(true)
                                                .build()))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.ACCOUNT_NOT_FOUND));
    }

    @Test
    void otherUsersCannotReadOrChangeMyAccounts() {
        User other = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 15), "other3@test.dev");

        assertThatThrownBy(() -> service.getAccount(other.getId(), primaryId)).isInstanceOf(AccountException.class);
        assertThatThrownBy(() -> service.getAccountTransactions(other.getId(), primaryId, null, null)).isInstanceOf(AccountException.class);
        assertThatThrownBy(() -> service.setPrimaryAccount(other.getId(), primaryId)).isInstanceOf(AccountException.class);
    }

    @Test
    void badDatesAreRejectedInsteadOfSilentlyIgnored() {
        assertThatThrownBy(() -> service.getAccountTransactions(user.getId(), primaryId, "2026-13-45", null))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.INVALID_INPUT));
        assertThatThrownBy(() -> service.getAccountTransactions(user.getId(), primaryId, "20261201", "20261101"))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.INVALID_INPUT));
        // 두 형식 모두 받는다.
        assertThat(service.getAccountTransactions(user.getId(), primaryId, "2026-01-01", "20261231").transactions()).isEmpty();
    }
}
