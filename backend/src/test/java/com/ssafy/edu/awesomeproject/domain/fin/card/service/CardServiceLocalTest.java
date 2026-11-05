package com.ssafy.edu.awesomeproject.domain.fin.card.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.fin.FinFixtures;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountStatus;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.CardRegisterRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.MockCardTransactionRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.Card;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import jakarta.persistence.EntityManager;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.util.ReflectionTestUtils;

/** 카드 서비스가 외부 카드사 없이 로컬 DB 만으로 동작하는지, 그리고 남의 카드를 못 보는지 확인한다. */
@DataJpaTest
@Import(CardService.class)
class CardServiceLocalTest {

    @Autowired private CardService service;
    @Autowired private CardRepository cards;
    @Autowired private CardTransactionRepository cardTransactions;
    @Autowired private AccountRepository accounts;
    @Autowired private EntityManager em;
    @Autowired private JdbcTemplate jdbc;

    @MockitoBean private AiClient aiClient;
    @MockitoBean private MonthlyTransactionFingerprintService fingerprintService;

    private User user;
    private User other;

    @BeforeEach
    void setUp() {
        // 싱글턴 빈이라 '꺼짐' 테스트가 바꾼 값이 다음 테스트로 새지 않게 매번 켠다.
        ReflectionTestUtils.setField(service, "mockDataEnabled", true);
        user = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 14), "card@test.dev");
        other = FinFixtures.user(em, FinFixtures.cohort(jdbc, em, 15), "card2@test.dev");
    }

    private Account demandAccount(User owner, String number, boolean primary) {
        return accounts.save(
                Account.builder()
                        .userId(owner.getId())
                        .accountNo(number)
                        .bankCode("999")
                        .bankName("DON'T 은행")
                        .accountRole(AccountRole.LINKED_DEPOSIT)
                        .isPrimary(primary)
                        .balance(BigDecimal.ZERO)
                        .status(AccountStatus.ACTIVE)
                        .build());
    }

    @Test
    void listIsReadFromTheLocalDatabaseAndNeverCallsOut() {
        assertThat(service.getCardList(user.getId()).getCards()).isEmpty();

        service.registerCard(user.getId(), new CardRegisterRequest("신한카드", "Deep Dream", "15"));
        CardListResponse list = service.getCardList(user.getId());

        assertThat(list.isSuccess()).isTrue();
        assertThat(list.getCards()).extracting(CardListResponse.CardItem::getCardName).containsExactly("Deep Dream");
        org.mockito.Mockito.verifyNoInteractions(aiClient);
    }

    @Test
    void registeredCardWithdrawsFromThePrimaryAccountOnTheChosenDay() {
        demandAccount(user, "9990000000000009", false);
        demandAccount(user, "9990000000000001", true);

        CardListResponse.CardItem item =
                service.registerCard(user.getId(), new CardRegisterRequest("국민카드", "청춘대로", "20"));

        Card card = cards.findById(item.getId()).orElseThrow();
        assertThat(card.getWithdrawalAccountNo()).isEqualTo("9990000000000001");
        assertThat(card.getWithdrawalDate()).isEqualTo("20");
        assertThat(card.getCardNo()).startsWith("9").hasSize(16);
        assertThat(card.getUser().getId()).isEqualTo(user.getId());
        // 결제일을 안 주면 1일
        CardListResponse.CardItem defaulted =
                service.registerCard(user.getId(), new CardRegisterRequest("우리카드", "카드의정석", null));
        assertThat(cards.findById(defaulted.getId()).orElseThrow().getWithdrawalDate()).isEqualTo("1");
    }

    @Test
    void mockTransactionIsStoredWithTheCardOwnerAndCountsInTheMonthlyExpense() {
        CardListResponse.CardItem item = service.registerCard(user.getId(), new CardRegisterRequest("신한카드", "Deep Dream", "15"));

        CardTransactionResponse.TransactionItem saved =
                service.addMockTransaction(
                        user.getId(), item.getId(), new MockCardTransactionRequest("스타벅스", "카페/디저트", 4_500L, null));
        service.addMockTransaction(
                user.getId(),
                item.getId(),
                new MockCardTransactionRequest("쿠팡", "쇼핑", 30_000L, LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)));

        assertThat(saved.getTransactionDate()).isEqualTo(LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE));
        assertThat(cardTransactions.findAll()).allSatisfy(t -> assertThat(t.getUserId()).isEqualTo(user.getId()));
        assertThat(service.getCardList(user.getId()).getCards().get(0).getMonthlyCardExpense())
                .isEqualTo(34_500L);
    }

    @Test
    void mockDataEndpointsAreOffUnlessEnabled() {
        ReflectionTestUtils.setField(service, "mockDataEnabled", false);

        assertThatThrownBy(() -> service.registerCard(user.getId(), new CardRegisterRequest("a", "b", "1")))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.MOCK_DATA_DISABLED));
        assertThatThrownBy(
                        () -> service.addMockTransaction(user.getId(), 1L, new MockCardTransactionRequest("m", null, 1L, null)))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.MOCK_DATA_DISABLED));
        assertThat(cards.count()).isZero();
    }

    @Test
    void otherUsersCannotSeeOrWriteToMyCard() {
        CardListResponse.CardItem mine = service.registerCard(user.getId(), new CardRegisterRequest("신한카드", "Deep Dream", "15"));
        service.addMockTransaction(user.getId(), mine.getId(), new MockCardTransactionRequest("스타벅스", "카페", 4_500L, null));
        String today = LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE);

        // 카드 상세는 예전에 카드 id 만으로 조회돼서 다른 사용자의 카드 이름과 결제 총액이 보였다.
        assertThatThrownBy(() -> service.getCardItem(other.getId(), mine.getId(), today, today))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.getCardTransactions(other.getId(), mine.getId(), today, today))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(
                        () -> service.addMockTransaction(other.getId(), mine.getId(), new MockCardTransactionRequest("m", null, 1L, null)))
                .isInstanceOfSatisfying(
                        AccountException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(AccountErrorCode.ACCOUNT_NOT_FOUND));

        assertThat(service.getCardItem(user.getId(), mine.getId(), today, today).getMonthlyCardExpense()).isEqualTo(4_500L);
    }
}
