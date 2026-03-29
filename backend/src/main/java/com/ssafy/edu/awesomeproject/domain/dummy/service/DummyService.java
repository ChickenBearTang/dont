package com.ssafy.edu.awesomeproject.domain.dummy.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.SignupService;
import com.ssafy.edu.awesomeproject.domain.auth.token.EmailVerificationStore;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import com.ssafy.edu.awesomeproject.domain.dummy.client.FinanceMemberClient;
import com.ssafy.edu.awesomeproject.domain.dummy.client.DummyCardClient;
import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.request.DummyCreateCreditCardRequest;
import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.response.DummyCreateCreditCardResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.request.FinanceMemberCreateRequest;
import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.response.FinanceMemberSearchResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateAccountsResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateAllResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateCardResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateCardTransactionsResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateUserResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.SavingsSettingResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.AccountService;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.Card;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.service.CardService;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import jakarta.persistence.EntityManager;
import java.math.BigDecimal;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClientResponseException;

@Service
@RequiredArgsConstructor
public class DummyService {
    private static final LocalDate DUMMY_BIRTH_DATE = LocalDate.of(1996, 5, 7);
    private static final String DUMMY_EMAIL_DOMAIN = "@ssafy.com";
    private static final String SAVE_BOX_ACCOUNT_TYPE_UNIQUE_NO = "999-1-792bcf290d6a48";
    private static final String PRIMARY_ACCOUNT_TYPE_UNIQUE_NO = "088-1-eacd56391e8e4a";
    private static final String DUMMY_CARD_UNIQUE_NO = "1009-b3f6f6e4f97c404";
    private static final String DUMMY_CARD_WITHDRAWAL_DATE = "1";
    private static final String DUMMY_SAVINGS_KEYWORD = "dummy";
    private static final BigDecimal DUMMY_SAVINGS_AMOUNT = BigDecimal.valueOf(10000);

    private final SignupService signupService;
    private final CohortRepository cohortRepository;
    private final UserRepository userRepository;
    private final EmailVerificationStore emailVerificationStore;
    private final FinanceMemberClient financeMemberClient;
    private final DummyCardClient dummyCardClient;
    private final AccountService accountService;
    private final CardService cardService;
    private final CardRepository cardRepository;
    private final CardTransactionRepository cardTransactionRepository;
    private final OpenBankAdapter openBankAdapter;
    private final EntityManager entityManager;

    @Value("${ssafy.api.key}")
    private String ssafyApiKey;

    @Value("${auth.email-verification.verified-ttl-seconds}")
    private long verifiedTtlSeconds;

    @Transactional
    public DummyCreateAllResponse createDummyAll(Integer generationNo) {
        DummyCreateUserResponse user = createDummyUser(generationNo);
        DummyCreateAccountsResponse accounts = createDummyAccounts(user.userId());
        DummyCreateCardResponse card = createDummyCard(user.userId());
        DummyCreateCardTransactionsResponse cardTransactions =
                createDummyCardTransactions(user.userId());

        return new DummyCreateAllResponse(generationNo, user, accounts, card, cardTransactions);
    }

    @Transactional
    public DummyCreateUserResponse createDummyUser(Integer generationNo) {
        Long cohortId =
                cohortRepository
                        .findByGenerationNo(generationNo)
                        .orElseThrow(() -> new AuthException(CommunityErrorCode.COHORT_NOT_FOUND))
                        .getId();

        int sequence = findNextDummySequence(generationNo);
        String identity = generationNo + "_dummy_" + sequence;
        String email = identity + DUMMY_EMAIL_DOMAIN;

        emailVerificationStore.markVerified(email, Duration.ofSeconds(verifiedTtlSeconds));
        signupService.signup(email, generateDummyPassword(), identity, DUMMY_BIRTH_DATE, true, cohortId);

        User createdUser =
                userRepository
                        .findByEmail(email)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
        createdUser.changeNickname(identity);

        String financeUserKey = issueOrFindFinanceUserKey(email);
        if (userRepository.existsBySsafyFinanceUserKey(financeUserKey)) {
            throw new AccountException(AccountErrorCode.DUPLICATE_FINANCE_KEY);
        }
        createdUser.updateSsafyFinanceUserKey(financeUserKey);

        return new DummyCreateUserResponse(
                createdUser.getId(),
                generationNo,
                sequence,
                createdUser.getEmail(),
                createdUser.getName(),
                createdUser.getNickname(),
                createdUser.getSsafyFinanceUserKey());
    }

    public DummyCreateAccountsResponse createDummyAccounts(Long userId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
        String userKey = user.getSsafyFinanceUserKey();
        if (userKey == null || userKey.isBlank()) {
            throw new AccountException(AccountErrorCode.FINANCE_USER_KEY_NOT_FOUND);
        }

        AccountCreateResponse saveBoxResponse =
                accountService.createSaveBox(
                        userId, new SaveBoxCreateRequest(SAVE_BOX_ACCOUNT_TYPE_UNIQUE_NO));

        OpenBankCreateAccountResponse primaryCreateResponse =
                openBankAdapter.createDemandDepositAccount(userKey, PRIMARY_ACCOUNT_TYPE_UNIQUE_NO);
        validateCreateAccountResponse(primaryCreateResponse);

        String primaryAccountNo = primaryCreateResponse.getRec().getAccountNo();
        AccountListResponse refreshed = accountService.refreshAccountList(userId);
        Long saveBoxAccountId =
                refreshed.accounts().stream()
                        .filter(account -> saveBoxResponse.accountNo().equals(account.accountNo()))
                        .map(AccountListResponse.AccountDetail::id)
                        .filter(id -> id != null)
                        .findFirst()
                        .orElseThrow(() -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));
        Long primaryAccountId =
                refreshed.accounts().stream()
                        .filter(account -> primaryAccountNo.equals(account.accountNo()))
                        .map(AccountListResponse.AccountDetail::id)
                        .filter(id -> id != null)
                        .findFirst()
                        .orElseThrow(() -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));

        accountService.setPrimaryAccount(userId, primaryAccountId);
        SavingsSettingResponse savingsSetting =
                accountService.createOrUpdateSavingsSetting(
                        userId,
                        SavingsSettingRequest.builder()
                                .primaryAccountId(primaryAccountId)
                                .saveboxAccountId(saveBoxAccountId)
                                .keyword(DUMMY_SAVINGS_KEYWORD)
                                .savingsAmount(DUMMY_SAVINGS_AMOUNT)
                                .isActive(true)
                                .build());

        return new DummyCreateAccountsResponse(
                userId,
                saveBoxResponse.accountNo(),
                saveBoxAccountId,
                primaryAccountNo,
                primaryAccountId,
                savingsSetting.id());
    }

    public DummyCreateCardResponse createDummyCard(Long userId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AccountException(AccountErrorCode.USER_NOT_FOUND));
        String userKey = user.getSsafyFinanceUserKey();
        if (userKey == null || userKey.isBlank()) {
            throw new AccountException(AccountErrorCode.FINANCE_USER_KEY_NOT_FOUND);
        }

        String withdrawalAccountNo =
                accountService.getAccountList(userId).accounts().stream()
                        .filter(account -> Boolean.TRUE.equals(account.isPrimary()))
                        .map(AccountListResponse.AccountDetail::accountNo)
                        .findFirst()
                        .orElseThrow(() -> new AccountException(AccountErrorCode.PRIMARY_ACCOUNT_NOT_FOUND));

        DummyCreateCreditCardResponse createCardResponse =
                dummyCardClient.createCreditCard(
                        DummyCreateCreditCardRequest.builder()
                                .header(createCreditCardHeader(userKey))
                                .cardUniqueNo(DUMMY_CARD_UNIQUE_NO)
                                .withdrawalAccountNo(withdrawalAccountNo)
                                .withdrawalDate(DUMMY_CARD_WITHDRAWAL_DATE)
                                .build());
        validateCreateCardResponse(createCardResponse);

        CardListResponse refreshed = cardService.refreshCardList(userId);
        int refreshedCardCount = refreshed.getCards() == null ? 0 : refreshed.getCards().size();

        return new DummyCreateCardResponse(
                userId, DUMMY_CARD_UNIQUE_NO, withdrawalAccountNo, refreshedCardCount);
    }

    @Transactional
    public DummyCreateCardTransactionsResponse createDummyCardTransactions(Long userId) {
        Card card =
                cardRepository.findAllByUser_Id(userId).stream()
                        .max(Comparator.comparing(Card::getId))
                        .orElseThrow(() -> new AccountException(AccountErrorCode.ACCOUNT_NOT_FOUND));

        LocalDate startDate = LocalDate.of(LocalDate.now().getYear(), 1, 1);
        LocalDate endDate = resolveEndDate(LocalDate.now().getYear());

        entityManager
                .createNativeQuery(
                        "delete from card_transactions where card_id = :cardId and transaction_date between :startDate and :endDate")
                .setParameter("cardId", card.getId())
                .setParameter("startDate", startDate)
                .setParameter("endDate", endDate)
                .executeUpdate();

        int insertedCount = 0;
        long totalAmount = 0L;

        for (Map.Entry<YearMonth, Map<String, Long>> monthly :
                buildMonthlyCategoryTemplate(startDate.getYear()).entrySet()) {
            YearMonth yearMonth = monthly.getKey();
            Map<String, Long> categoryBaseAmounts = monthly.getValue();
            LocalDate monthEnd = resolveMonthEnd(yearMonth);

            for (Map.Entry<String, Long> categoryEntry : categoryBaseAmounts.entrySet()) {
                String category = categoryEntry.getKey();
                long randomizedAmount = randomizeAmount(categoryEntry.getValue());
                LocalDate transactionDate = randomDateWithin(yearMonth.atDay(1), monthEnd);

                entityManager
                        .createNativeQuery(
                                "insert into card_transactions "
                                        + "(card_id, transaction_date, merchant_name, category_name, transaction_amount, transaction_type, approval_no, description, user_id) "
                                        + "values (:cardId, :transactionDate, :merchantName, :categoryName, :transactionAmount, :transactionType, :approvalNo, :description, :userId)")
                        .setParameter("cardId", card.getId())
                        .setParameter("transactionDate", transactionDate)
                        .setParameter("merchantName", category + " 더미가맹점")
                        .setParameter("categoryName", category)
                        .setParameter("transactionAmount", randomizedAmount)
                        .setParameter("transactionType", "PAYMENT")
                        .setParameter("approvalNo", randomApprovalNo())
                        .setParameter("description", "dummy monthly aggregate")
                        .setParameter("userId", userId)
                        .executeUpdate();
                insertedCount++;
                totalAmount += randomizedAmount;
            }
        }

        return new DummyCreateCardTransactionsResponse(
                userId,
                card.getId(),
                startDate.toString(),
                endDate.toString(),
                insertedCount,
                totalAmount);
    }

    private int findNextDummySequence(Integer generationNo) {
        int sequence = 1;
        while (userRepository.existsByEmail(buildEmail(generationNo, sequence))) {
            sequence++;
        }
        return sequence;
    }

    private String buildEmail(Integer generationNo, int sequence) {
        return generationNo + "_dummy_" + sequence + DUMMY_EMAIL_DOMAIN;
    }

    private String generateDummyPassword() {
        return "dummy-" + UUID.randomUUID() + "-A1!";
    }

    private String issueOrFindFinanceUserKey(String email) {
        FinanceMemberCreateRequest request = new FinanceMemberCreateRequest(ssafyApiKey, email);
        try {
            financeMemberClient.createMember(request);
        } catch (RestClientResponseException exception) {
            if (!isAlreadyExistsResponse(exception)) {
                throw exception;
            }
        }

        FinanceMemberSearchResponse existing = findExistingMember(request);
        validateMemberSearchResponse(existing, email);
        return existing.userKey();
    }

    private FinanceMemberSearchResponse findExistingMember(FinanceMemberCreateRequest request) {
        try {
            return financeMemberClient.searchMember(request);
        } catch (RestClientResponseException ignored) {
            try {
                return financeMemberClient.inquireMember(request);
            } catch (RestClientResponseException exception) {
                throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
            }
        }
    }

    private boolean isAlreadyExistsResponse(RestClientResponseException exception) {
        if (exception.getStatusCode().value() == 409) {
            return true;
        }

        String responseBody = exception.getResponseBodyAsString();
        if (responseBody == null || responseBody.isBlank()) {
            return false;
        }

        String normalized = responseBody.toLowerCase(Locale.ROOT);
        return normalized.contains("already")
                || normalized.contains("exists")
                || normalized.contains("이미")
                || normalized.contains("존재");
    }

    private void validateMemberSearchResponse(
            FinanceMemberSearchResponse response, String expectedUserId) {
        if (response == null || response.userKey() == null || response.userKey().isBlank()) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }
        if (response.userId() == null || response.userId().isBlank()) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }
        if (!response.userId().equalsIgnoreCase(expectedUserId)) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }
    }

    private void validateCreateAccountResponse(OpenBankCreateAccountResponse response) {
        if (response == null || response.getHeader() == null || response.getRec() == null) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }

        String responseCode = response.getHeader().getResponseCode();
        if (!"201".equals(responseCode) && !"H0000".equals(responseCode)) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }
    }

    private OpenBankReqHeader createCreditCardHeader(String userKey) {
        LocalDateTime now = LocalDateTime.now();
        return OpenBankReqHeader.builder()
                .apiName("createCreditCard")
                .transmissionDate(now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                .transmissionTime(now.format(DateTimeFormatter.ofPattern("HHmmss")))
                .institutionCode("00100")
                .fintechAppNo("001")
                .apiServiceCode("createCreditCard")
                .institutionTransactionUniqueNo(generateUniqueNo(now))
                .apiKey(ssafyApiKey)
                .userKey(userKey)
                .build();
    }

    private String generateUniqueNo(LocalDateTime now) {
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        int randomNo = ThreadLocalRandom.current().nextInt(100000, 1000000);
        return timestamp + randomNo;
    }

    private void validateCreateCardResponse(DummyCreateCreditCardResponse response) {
        if (response == null || response.getHeader() == null) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }

        String responseCode = response.getHeader().getResponseCode();
        if (!"201".equals(responseCode) && !"H0000".equals(responseCode)) {
            throw new AccountException(AccountErrorCode.API_RESPONSE_ERROR);
        }
    }

    private Map<YearMonth, Map<String, Long>> buildMonthlyCategoryTemplate(int year) {
        Map<YearMonth, Map<String, Long>> template = new LinkedHashMap<>();

        template.put(
                YearMonth.of(year, 1),
                Map.of(
                        "식사/음식", 130_000L,
                        "카페/디저트", 70_000L,
                        "편의점/마트", 120_000L,
                        "문화/여가", 90_000L,
                        "의료/건강", 60_000L));
        template.put(
                YearMonth.of(year, 2),
                Map.of(
                        "식사/음식", 115_000L,
                        "카페/디저트", 65_000L,
                        "편의점/마트", 80_000L,
                        "문화/여가", 85_000L,
                        "의료/건강", 55_000L));
        template.put(
                YearMonth.of(year, 3),
                Map.of(
                        "식사/음식", 120_000L,
                        "카페/디저트", 60_000L,
                        "편의점/마트", 90_000L,
                        "문화/여가", 75_000L,
                        "의료/건강", 50_000L));
        return template;
    }

    private LocalDate resolveEndDate(int year) {
        LocalDate march27 = LocalDate.of(year, 3, 27);
        LocalDate now = LocalDate.now();
        return now.isBefore(march27) ? now : march27;
    }

    private LocalDate resolveMonthEnd(YearMonth yearMonth) {
        LocalDate endDate = resolveEndDate(yearMonth.getYear());
        LocalDate monthEnd = yearMonth.atEndOfMonth();
        return endDate.isBefore(monthEnd) && endDate.getMonthValue() == yearMonth.getMonthValue()
                ? endDate
                : monthEnd;
    }

    private long randomizeAmount(long baseAmount) {
        double multiplier = ThreadLocalRandom.current().nextDouble(0.85, 1.16);
        long raw = Math.round(baseAmount * multiplier);
        return Math.max(5_000L, (raw / 100L) * 100L);
    }

    private LocalDate randomDateWithin(LocalDate start, LocalDate end) {
        if (end.isBefore(start)) {
            return start;
        }
        long daySpan = end.toEpochDay() - start.toEpochDay();
        long offset = ThreadLocalRandom.current().nextLong(daySpan + 1);
        return start.plusDays(offset);
    }

    private String randomApprovalNo() {
        int number = ThreadLocalRandom.current().nextInt(100000, 1000000);
        return "APP" + number;
    }
}
