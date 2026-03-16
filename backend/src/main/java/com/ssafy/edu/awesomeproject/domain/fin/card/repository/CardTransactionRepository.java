package com.ssafy.edu.awesomeproject.domain.fin.card.repository;

import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CardTransactionRepository extends JpaRepository<CardTransaction, Long> {
    List<CardTransaction> findByCardIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
        Long cardId,
        LocalDate startDate,
        LocalDate endDate);
}
