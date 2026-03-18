package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.PrEvent;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PrEventRepository extends JpaRepository<PrEvent, Long> {
    List<PrEvent> findAllByPostIdOrderByCreatedAtAsc(Long postId);
}
