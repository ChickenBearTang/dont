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
            """
            select ct.id as id,
                   ct.transactionDate as transactionDate,
                   ct.transactionTime as transactionTime,
                   ct.transactionAmount as transactionAmount,
                   ct.merchantName as merchantName,
                   ct.categoryName as categoryName
            from CardTransaction ct
            where ct.userId = :userId
              and ct.transactionDate between :startDate and :endDate
            order by ct.transactionDate asc, ct.transactionTime asc, ct.id asc
            """)
    List<MonthlyTransactionFingerprintProjection> findMonthlyTransactionsForFingerprint(
            @Param("userId") Long userId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);

    @Query(
            """
            select count(ct) as txCount,
                   coalesce(sum(ct.transactionAmount), 0) as totalAmount,
                   max(ct.transactionDate) as lastDate,
                   max(ct.transactionTime) as lastTime
            from CardTransaction ct
            where ct.userId = :userId
              and ct.transactionDate between :startDate and :endDate
            """)
    MonthlyTransactionSnapshotProjection findMonthlyTransactionSnapshot(
            @Param("userId") Long userId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);

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

    interface MonthlyTransactionSnapshotProjection {
        Long getTxCount();

        Long getTotalAmount();

        LocalDate getLastDate();

        String getLastTime();
    }

    interface MonthlyTransactionFingerprintProjection {
        Long getId();

        LocalDate getTransactionDate();

        String getTransactionTime();

        Long getTransactionAmount();

        String getMerchantName();

        String getCategoryName();
    }

    @Query(
            value =
                    """
                    with cohort_users as (
                        select distinct u.id
                        from users u
                        where u.cohort_id = :cohortId
                           or u.id = :userId
                    ),
                    user_spending as (
                        select
                            cu.id as user_id,
                            coalesce(sum(case when ct.category_name in ('식사/외식', '식사/음식') then ct.transaction_amount else 0 end), 0) as food_amount,
                            coalesce(sum(case when ct.category_name in ('카페/간식', '카페/디저트') then ct.transaction_amount else 0 end), 0) as cafe_amount,
                            coalesce(sum(case when ct.category_name = '문화/여가' then ct.transaction_amount else 0 end), 0) as culture_amount,
                            coalesce(sum(case when ct.category_name in ('쇼핑/마트', '편의점/마트') then ct.transaction_amount else 0 end), 0) as market_amount,
                            coalesce(sum(case when ct.category_name = '의료/건강' then ct.transaction_amount else 0 end), 0) as medical_amount
                        from cohort_users cu
                        left join card_transactions ct
                          on ct.user_id = cu.id
                         and ct.transaction_date between :startDate and :endDate
                        group by cu.id
                    )
                    select
                        cast(:cohortId as bigint) as cohortId,
                        coalesce(round(avg(user_spending.food_amount), 0), 0) as avgFood,
                        coalesce(round(avg(user_spending.cafe_amount), 0), 0) as avgCafe,
                        coalesce(round(avg(user_spending.culture_amount), 0), 0) as avgCulture,
                        coalesce(round(avg(user_spending.market_amount), 0), 0) as avgMarket,
                        coalesce(round(avg(user_spending.medical_amount), 0), 0) as avgMedical
                    from user_spending
                    """,
            nativeQuery = true)
    CohortCategoryAverageProjection findCohortCategoryAverages(
            @Param("cohortId") Long cohortId,
            @Param("userId") Long userId,
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
