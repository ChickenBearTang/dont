package com.ssafy.edu.awesomeproject.domain.fin.profile.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.profile.dto.response.FinanceProfileResponse;
import java.time.DateTimeException;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class FinanceProfileService {

    private static final DateTimeFormatter BASIC_DATE = DateTimeFormatter.BASIC_ISO_DATE;
    private static final DateTimeFormatter ISO_DATE = DateTimeFormatter.ISO_LOCAL_DATE;

    private final AccountRepository accountRepository;
    private final CardRepository cardRepository;
    private final CardTransactionRepository cardTransactionRepository;

    public FinanceProfileService(
            AccountRepository accountRepository,
            CardRepository cardRepository,
            CardTransactionRepository cardTransactionRepository) {
        this.accountRepository = accountRepository;
        this.cardRepository = cardRepository;
        this.cardTransactionRepository = cardTransactionRepository;
    }

    @Transactional(readOnly = true)
    public FinanceProfileResponse getFinanceProfile(String rawUserId) {
        Long userId = normalizeUserId(rawUserId);
        double currentBalance = accountRepository.sumBalanceByUserId(userId).doubleValue();

        double emergencyFundBalance =
                accountRepository.sumBalanceByUserIdAndRole(userId, AccountRole.SAVE_BOX).doubleValue();

        LocalDate today = LocalDate.now();
        LocalDate monthStart = today.withDayOfMonth(1);
        Long expectedAmountValue =
                cardTransactionRepository.sumAmountByUserIdAndDateRange(userId, monthStart, today);
        double expectedCardPaymentAmount =
                expectedAmountValue == null ? 0.0 : expectedAmountValue.doubleValue();

        int daysUntilCardDue =
                cardRepository.findWithdrawalDatesByUserId(userId).stream()
                        .map(this::computeDaysUntilDue)
                        .filter(value -> value >= 0)
                        .min(Integer::compareTo)
                        .orElse(14);

        return new FinanceProfileResponse(
                currentBalance,
                emergencyFundBalance,
                expectedCardPaymentAmount,
                daysUntilCardDue);
    }

    private Long normalizeUserId(String rawUserId) {
        if (rawUserId == null || rawUserId.isBlank()) {
            throw new IllegalArgumentException("userId is required");
        }
        String normalized = rawUserId.trim();
        if (normalized.startsWith("U") || normalized.startsWith("u")) {
            normalized = normalized.substring(1);
        }
        return Long.parseLong(normalized);
    }

    private int computeDaysUntilDue(String rawWithdrawalDate) {
        if (rawWithdrawalDate == null || rawWithdrawalDate.isBlank()) {
            return 14;
        }

        String value = rawWithdrawalDate.trim();
        LocalDate today = LocalDate.now();

        try {
            LocalDate dueDate = LocalDate.parse(value, BASIC_DATE);
            return (int) today.until(dueDate).getDays();
        } catch (DateTimeException ignored) {

        }

        try {
            LocalDate dueDate = LocalDate.parse(value, ISO_DATE);
            return (int) today.until(dueDate).getDays();
        } catch (DateTimeException ignored) {

        }

        try {
            int dayOfMonth = Integer.parseInt(value);
            int safeDay = Math.max(1, Math.min(dayOfMonth, 28));
            LocalDate candidate = YearMonth.from(today).atDay(safeDay);
            if (candidate.isBefore(today)) {
                candidate = YearMonth.from(today.plusMonths(1)).atDay(safeDay);
            }
            return (int) today.until(candidate).getDays();
        } catch (NumberFormatException ignored) {
            return 14;
        }
    }
}
