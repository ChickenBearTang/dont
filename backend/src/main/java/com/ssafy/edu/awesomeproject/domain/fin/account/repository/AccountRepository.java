package com.ssafy.edu.awesomeproject.domain.fin.account.repository;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole;
import jakarta.persistence.LockModeType;
import java.math.BigDecimal;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AccountRepository extends JpaRepository<Account, Long> {

    Optional<Account> findByAccountNo(String accountNo);

    boolean existsByAccountNo(String accountNo);

    List<Account> findAllByUserId(Long userId);

    @Query("select coalesce(sum(a.balance), 0) from Account a where a.userId = :userId")
    BigDecimal sumBalanceByUserId(@Param("userId") Long userId);

    @Query(
            "select coalesce(sum(a.balance), 0) from Account a where a.userId = :userId and a.accountRole = :accountRole")
    BigDecimal sumBalanceByUserIdAndRole(
            @Param("userId") Long userId,
            @Param("accountRole") AccountRole accountRole);

    List<Account> findAllByAccountRole(AccountRole accountRole);

    Optional<Account> getAccountById(Long id);

    /**
     * 잔액을 바꾸는 쪽이 쓰는 행 잠금 조회. 여러 계좌를 잠글 때는 반드시 id 오름차순으로 잠가야 교착이 안
     * 난다 (LedgerService.lockInOrder).
     */
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select a from Account a where a.id = :id")
    Optional<Account> findByIdForUpdate(@Param("id") Long id);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select a from Account a where a.id in :ids order by a.id asc")
    List<Account> findAllByIdInForUpdateOrderById(@Param("ids") Collection<Long> ids);
}
