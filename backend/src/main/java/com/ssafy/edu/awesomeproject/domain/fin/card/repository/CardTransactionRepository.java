package com.ssafy.edu.awesomeproject.domain.fin.card.repository;

import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import java.math.BigDecimal;
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
            "select coalesce(sum(ct.transactionAmount), 0) from CardTransaction ct where ct.userId = :userId and ct.transactionDate between :startDate and :endDate")
    Long sumAmountByUserIdAndDateRange(
            @Param("userId") Long userId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);

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

    @Query(
            value =
                    """
                    with cohort_users as (
                        select u.id
                        from users u
                        where u.cohort_id = :cohortId
                    ),
                    user_spending as (
                        select
                            cu.id as user_id,
                            coalesce(sum(case when ct.category_name = '식사/외식' then ct.transaction_amount else 0 end), 0) as food_amount,
                            coalesce(sum(case when ct.category_name = '카페/간식' then ct.transaction_amount else 0 end), 0) as cafe_amount,
                            coalesce(sum(case when ct.category_name = '문화/여가' then ct.transaction_amount else 0 end), 0) as culture_amount,
                            coalesce(sum(case when ct.category_name = '쇼핑/마트' then ct.transaction_amount else 0 end), 0) as market_amount,
                            coalesce(sum(case when ct.category_name = '의료/건강' then ct.transaction_amount else 0 end), 0) as medical_amount
                        from cohort_users cu
                        left join card_transactions ct
                          on ct.user_id = cu.id
                         and ct.transaction_date between :startDate and :endDate
                        group by cu.id
                    )
                    select
                        cast(:cohortId as bigint) as cohortId,
                        coalesce(avg(user_spending.food_amount), 0) as avgFood,
                        coalesce(avg(user_spending.cafe_amount), 0) as avgCafe,
                        coalesce(avg(user_spending.culture_amount), 0) as avgCulture,
                        coalesce(avg(user_spending.market_amount), 0) as avgMarket,
                        coalesce(avg(user_spending.medical_amount), 0) as avgMedical
                    from user_spending
                    """,
            nativeQuery = true)
    CohortCategoryAverageProjection findCohortCategoryAverages(
            @Param("cohortId") Long cohortId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);

    interface CohortCategoryAverageProjection {
        Long getCohortId();

        BigDecimal getAvgFood();

        BigDecimal getAvgCafe();

        BigDecimal getAvgCulture();

        BigDecimal getAvgMarket();

        BigDecimal getAvgMedical();
    }

}
