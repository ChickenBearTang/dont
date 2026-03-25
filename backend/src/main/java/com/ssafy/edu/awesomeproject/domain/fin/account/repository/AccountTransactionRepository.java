package com.ssafy.edu.awesomeproject.domain.fin.account.repository;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountTransactionRepository extends JpaRepository<AccountTransaction, Long> {
    Optional<AccountTransaction> findByTransactionUniqueNo(String transactionUniqueNo);

    List<AccountTransaction> findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(
        Long accountId);

    List<AccountTransaction>
    findAllByAccountIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
        Long accountId, LocalDate startDate, LocalDate endDate);

    List<AccountTransaction> findAllByAccountIdAndAutoSavingsProcessedFalse(Long accountId);
}
