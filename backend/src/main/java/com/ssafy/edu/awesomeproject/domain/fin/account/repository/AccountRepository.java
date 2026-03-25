package com.ssafy.edu.awesomeproject.domain.fin.account.repository;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountStatus;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AccountRepository extends JpaRepository<Account, Long> {

    Optional<Account> findByAccountNo(String accountNo);

    List<Account> findAllByUserId(Long userId);

    @Query(
            "select coalesce(sum(a.balance), 0) from Account a where a.userId = :userId and a.status = :status")
    BigDecimal sumBalanceByUserId(
            @Param("userId") Long userId, @Param("status") AccountStatus status);

    @Query(
            "select coalesce(sum(a.balance), 0) from Account a where a.userId = :userId and a.accountRole = :accountRole and a.status = :status")
    BigDecimal sumBalanceByUserIdAndRole(
            @Param("userId") Long userId,
            @Param("accountRole") AccountRole accountRole,
            @Param("status") AccountStatus status);
}
