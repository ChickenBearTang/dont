package com.ssafy.edu.awesomeproject.domain.fin.account.repository;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountTransaction;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AccountTransactionRepository extends JpaRepository<AccountTransaction, Long> {

    Optional<AccountTransaction> findByTransactionUniqueNo(String transactionUniqueNo);

    List<AccountTransaction> findAllByAccountIdOrderByTransactionDateDescTransactionTimeDesc(
        Long accountId);

    List<AccountTransaction>
    findAllByAccountIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
        Long accountId, LocalDate startDate, LocalDate endDate);

    /** 자동저축 검사를 아직 안 받은 입금. 입금 순서대로 처리하려고 id 오름차순이다. */
    List<AccountTransaction> findAllByAccountIdAndAutoSavingsProcessedFalseOrderByIdAsc(
        Long accountId);

    /** 사용자의 모든 계좌 거래 (소득·고정지출 추정용). 계좌는 한 번에 같이 읽는다. */
    @Query(
            """
            select t from AccountTransaction t join fetch t.account a
            where a.userId = :userId
              and t.transactionDate between :startDate and :endDate
            """)
    List<AccountTransaction> findAllByUserIdAndDateRange(
        @Param("userId") Long userId,
        @Param("startDate") LocalDate startDate,
        @Param("endDate") LocalDate endDate);
}
