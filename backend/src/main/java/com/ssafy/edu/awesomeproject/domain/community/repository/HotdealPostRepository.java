package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.HotdealPost;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HotdealPostRepository extends JpaRepository<HotdealPost, Long> {
    Optional<HotdealPost> findByPost_Id(Long postId);

    List<HotdealPost> findByPostIdIn(Collection<Long> postIds);
}
