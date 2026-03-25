package com.ssafy.edu.awesomeproject.domain.fin.card.repository;

import com.ssafy.edu.awesomeproject.domain.fin.card.entity.Card;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CardRepository extends JpaRepository<Card, Long> {
    List<Card> findAllByUser_Id(Long userId);

    void deleteByUser_Id(Long userId);

    Optional<Card> findByIdAndUserId(Long id, Long userId);

    @Query("select c.withdrawalDate from Card c where c.user.id = :userId")
    List<String> findWithdrawalDatesByUserId(@Param("userId") Long userId);
}
