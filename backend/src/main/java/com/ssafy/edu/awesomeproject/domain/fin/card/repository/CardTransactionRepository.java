package com.ssafy.edu.awesomeproject.domain.fin.card.repository;

import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CardTransactionRepository extends JpaRepository<CardTransaction, Long> {
    List<CardTransaction> findByCardIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
        Long cardId,
        LocalDate startDate,
        LocalDate endDate
    );

    //한 유저 + 날짜로 거래내역 필터링
    List<CardTransaction> findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
        Long userId,
        LocalDate startDate,
        LocalDate endDate
    );

}
