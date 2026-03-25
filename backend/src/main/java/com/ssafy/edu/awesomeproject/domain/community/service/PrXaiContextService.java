package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiEvaluationRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiFinanceProfileDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiProvenanceValueDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiPurchaseContextDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiRecentTransactionDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrPostRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.profile.dto.response.FinanceProfileResponse;
import com.ssafy.edu.awesomeproject.domain.fin.profile.service.FinanceProfileService;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PrXaiContextService {

    private static final DateTimeFormatter BASIC_DATE = DateTimeFormatter.BASIC_ISO_DATE;

    private final PrPostRepository prPostRepository;
    private final UserRepository userRepository;
    private final FinanceProfileService financeProfileService;
    private final CardTransactionRepository cardTransactionRepository;
    private final AccountRepository accountRepository;

    public PrXaiContextService(
            PrPostRepository prPostRepository,
            UserRepository userRepository,
            FinanceProfileService financeProfileService,
            CardTransactionRepository cardTransactionRepository,
            AccountRepository accountRepository) {
        this.prPostRepository = prPostRepository;
        this.userRepository = userRepository;
        this.financeProfileService = financeProfileService;
        this.cardTransactionRepository = cardTransactionRepository;
        this.accountRepository = accountRepository;
    }

    @Transactional(readOnly = true)
    public PrXaiEvaluationRequestDto buildContext(Long postId, Long userId) {
        if (userId == null) {
            throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_FORBIDDEN);
        }
        userRepository
                .findActiveById(userId)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));

        PrPost prPost =
                prPostRepository
                        .findByPost_Id(postId)
                        .orElseThrow(
                                () ->
                                        new CommunityException(
                                                CommunityErrorCode.PURCHASE_REQUEST_NOT_FOUND));

        Long purchaseRequesterId = prPost.getPost().getUser().getId();

        String todaySnapshot = LocalDate.now(ZoneOffset.UTC).format(BASIC_DATE);
        FinanceProfileResponse financeProfile =
                financeProfileService.getFinanceProfile(String.valueOf(purchaseRequesterId));
        BigDecimal saveboxBalance =
                accountRepository.sumBalanceByUserIdAndRole(purchaseRequesterId, AccountRole.SAVE_BOX);
        double saveboxBalanceValue = saveboxBalance == null ? 0d : saveboxBalance.doubleValue();
        if (saveboxBalanceValue <= 0d && financeProfile.emergencyFundBalance() > 0d) {
            saveboxBalanceValue = financeProfile.emergencyFundBalance();
        }
        List<PrXaiRecentTransactionDto> recentTransactions =
                buildRecentTransactions(purchaseRequesterId);

        return new PrXaiEvaluationRequestDto(
                UUID.randomUUID().toString(),
                "v1",
                "v1",
                new PrXaiPurchaseContextDto(
                        prPost.getPostId(),
                        prPost.getPost().getTitle(),
                        prPost.getItemName(),
                        prPost.getPost().getContent(),
                        prPost.getCategory(),
                        prPost.getPurchaseUrl(),
                        new PrXaiProvenanceValueDto(
                                prPost.getPriceAmount(),
                                "spring.pr_post",
                                "pr-post:%d:%s".formatted(prPost.getPostId(), todaySnapshot),
                                false,
                                false,
                                null)),
                new PrXaiFinanceProfileDto(
                        new PrXaiProvenanceValueDto(
                                financeProfile.currentBalance(),
                                "spring.finance_profile",
                                "finance-profile:%d:%s".formatted(purchaseRequesterId, todaySnapshot),
                                false,
                                false,
                                null),
                        new PrXaiProvenanceValueDto(
                                financeProfile.emergencyFundBalance(),
                                "spring.finance_profile",
                                "finance-profile:%d:%s".formatted(purchaseRequesterId, todaySnapshot),
                                false,
                                false,
                                null),
                        new PrXaiProvenanceValueDto(
                                saveboxBalanceValue,
                                "spring.savebox",
                                "savebox-balance:%d:%s".formatted(purchaseRequesterId, todaySnapshot),
                                false,
                                false,
                                null),
                        new PrXaiProvenanceValueDto(
                                financeProfile.expectedCardPaymentAmount(),
                                "spring.finance_profile",
                                "finance-profile:%d:%s".formatted(purchaseRequesterId, todaySnapshot),
                                false,
                                false,
                                null),
                        new PrXaiProvenanceValueDto(
                                financeProfile.daysUntilCardDue(),
                                "spring.finance_profile",
                                "finance-profile:%d:%s".formatted(purchaseRequesterId, todaySnapshot),
                                false,
                                false,
                                null)),
                recentTransactions);
    }

    private List<PrXaiRecentTransactionDto> buildRecentTransactions(Long userId) {
        LocalDate endDate = LocalDate.now(ZoneOffset.UTC);
        LocalDate startDate = endDate.minusMonths(3);
        return cardTransactionRepository
                .findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                        userId, startDate, endDate)
                .stream()
                .limit(50)
                .map(this::toRecentTransaction)
                .toList();
    }

    private PrXaiRecentTransactionDto toRecentTransaction(CardTransaction transaction) {
        String transactionDate =
                transaction.getTransactionDate() == null
                        ? ""
                        : transaction.getTransactionDate().format(BASIC_DATE);
        String rawTime =
                transaction.getTransactionTime() == null
                        ? "000000"
                        : transaction.getTransactionTime().replaceAll("[^0-9]", "");
        String transactionTime =
                rawTime.isBlank() ? "000000" : rawTime.substring(0, Math.min(6, rawTime.length()));
        long amountValue =
                transaction.getTransactionAmount() == null ? 0L : transaction.getTransactionAmount();
        int transactionAmount =
                amountValue > Integer.MAX_VALUE ? Integer.MAX_VALUE : (int) Math.max(amountValue, 0L);
        return new PrXaiRecentTransactionDto(
                transactionDate,
                transactionTime,
                transaction.getMerchantName() == null ? "" : transaction.getMerchantName(),
                transaction.getCategoryName() == null ? "" : transaction.getCategoryName(),
                transactionAmount);
    }
}
