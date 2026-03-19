package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.PollPost;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PollPostRepository extends JpaRepository<PollPost, Long> {
    Optional<PollPost> findByPost_Id(Long postId);

    List<PollPost> findByPostIdIn(Collection<Long> postIds);
}
