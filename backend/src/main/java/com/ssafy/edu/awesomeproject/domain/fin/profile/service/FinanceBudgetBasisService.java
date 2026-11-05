package com.ssafy.edu.awesomeproject.domain.fin.profile.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 사용자의 입출금 계좌 거래에서 월 소득/고정지출을 추정한다. 계산은 {@link MonthlyBudgetBasisEstimator}가 한다. */
@Service
public class FinanceBudgetBasisService {

    private final AccountRepository accountRepository;
    private final AccountTransactionRepository accountTransactionRepository;

    public FinanceBudgetBasisService(
            AccountRepository accountRepository,
            AccountTransactionRepository accountTransactionRepository) {
        this.accountRepository = accountRepository;
        this.accountTransactionRepository = accountTransactionRepository;
    }

    @Transactional(readOnly = true)
    public Optional<MonthlyBudgetBasisEstimator.Basis> estimate(Long userId) {
        return estimate(userId, LocalDate.now());
    }

    @Transactional(readOnly = true)
    public Optional<MonthlyBudgetBasisEstimator.Basis> estimate(Long userId, LocalDate today) {
        Set<String> ownAccountNos =
                accountRepository.findAllByUserId(userId).stream()
                        .map(Account::getAccountNo)
                        .collect(Collectors.toSet());

        List<MonthlyBudgetBasisEstimator.Entry> entries =
                accountTransactionRepository
                        .findAllByUserIdAndDateRange(
                                userId,
                                MonthlyBudgetBasisEstimator.windowStart(today),
                                MonthlyBudgetBasisEstimator.windowEnd(today))
                        .stream()
                        // 세이브박스 안의 입출금은 본인 계좌 이동의 반대편이다. 입출금 계좌만 본다.
                        .filter(tx -> tx.getAccount().getAccountRole() == AccountRole.LINKED_DEPOSIT)
                        .map(tx -> toEntry(tx, ownAccountNos))
                        .toList();
        return MonthlyBudgetBasisEstimator.estimate(entries, today);
    }

    private static MonthlyBudgetBasisEstimator.Entry toEntry(
            AccountTransaction tx, Set<String> ownAccountNos) {
        boolean internal =
                tx.getTransactionAccountNo() != null
                        && ownAccountNos.contains(tx.getTransactionAccountNo());
        long amount =
                tx.getTransactionAmount() == null ? 0L : tx.getTransactionAmount().longValue();
        return new MonthlyBudgetBasisEstimator.Entry(
                tx.getTransactionDate(),
                "1".equals(tx.getTransactionType()),
                amount,
                tx.getTransactionSummary(),
                tx.getTransactionMemo(),
                internal);
    }
}
