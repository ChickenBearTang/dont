package com.ssafy.edu.awesomeproject.domain.fin.card.repository;

import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CardTransactionRepository extends JpaRepository<CardTransaction, Long> {
    List<CardTransaction>
            findByCardIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                    Long cardId, LocalDate startDate, LocalDate endDate);

    List<CardTransaction>
            findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                    Long userId, LocalDate startDate, LocalDate endDate);

    @Query(
            """
            select ct.card.id as cardId, coalesce(sum(ct.transactionAmount), 0) as totalAmount
            from CardTransaction ct
            where ct.userId = :userId
              and ct.transactionDate between :startDate and :endDate
            group by ct.card.id
            """)
    List<CardMonthlyExpenseProjection> findMonthlyExpenseByUserIdAndDateRange(
            @Param("userId") Long userId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);

    interface CardMonthlyExpenseProjection {
        Long getCardId();

        Long getTotalAmount();
    }
}
