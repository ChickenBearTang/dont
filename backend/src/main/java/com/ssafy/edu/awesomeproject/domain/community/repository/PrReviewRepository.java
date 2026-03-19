package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.PrReview;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PrReviewRepository extends JpaRepository<PrReview, Long> {
    List<PrReview> findAllByPostIdOrderByCreatedAtAsc(Long postId);
}
