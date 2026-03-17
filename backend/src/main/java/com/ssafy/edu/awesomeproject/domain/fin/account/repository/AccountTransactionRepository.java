package com.ssafy.edu.awesomeproject.domain.fin.account.repository;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountTransactionRepository extends JpaRepository<AccountTransaction, Long> {
    Optional<AccountTransaction> findByTransactionUniqueNo(String transactionUniqueNo);
    java.util.List<AccountTransaction> findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(Long accountId);
}
