package com.ssafy.edu.awesomeproject.domain.fin.card.repository;

import com.ssafy.edu.awesomeproject.domain.fin.card.entity.Card;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CardRepository extends JpaRepository<Card, Long> {
    List<Card> findAllByUserId(Long userId);

    Optional<Card> findByUserIdAndCardNo(Long userId, String cardNo);

    Optional<Card> findByIdAndUserId(Long id, Long userId);

    void deleteByUserId(Long userId);
}
