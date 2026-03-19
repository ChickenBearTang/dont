package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PostRepository extends JpaRepository<Post, Long> {
    Optional<Post> findByIdAndStatus(Long id, PostStatus status);

    @EntityGraph(attributePaths = {"user", "board", "board.cohort"})
    Page<Post> findByBoard_IdAndStatus(
            Long boardId,
            PostStatus status,
            Pageable pageable);

    @EntityGraph(attributePaths = {"user", "board", "board.cohort"})
    Page<Post> findByBoard_IdInAndStatus(
            Iterable<Long> boardIds,
            PostStatus status,
            Pageable pageable);
}
