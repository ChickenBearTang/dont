package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PrPostRepository extends JpaRepository<PrPost, Long> {
    boolean existsByPost_Id(Long postId);

    Optional<PrPost> findByPost_Id(Long postId);

    List<PrPost> findByPostIdIn(Collection<Long> postIds);
}
