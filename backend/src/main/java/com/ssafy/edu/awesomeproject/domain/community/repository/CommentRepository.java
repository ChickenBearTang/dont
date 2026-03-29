package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Comment;
import com.ssafy.edu.awesomeproject.domain.community.entity.CommentStatus;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CommentRepository extends JpaRepository<Comment, Long> {
    Optional<Comment> findByIdAndStatus(Long id, CommentStatus status);

    Optional<Comment> findByIdAndStatusIn(Long id, Collection<CommentStatus> statuses);


    Page<Comment> findByPost_IdAndStatus(Long postId, CommentStatus status, Pageable pageable);

    Page<Comment> findByPost_IdAndStatusIn(
            Long postId, Collection<CommentStatus> statuses, Pageable pageable);

    List<Comment> findByPost_IdAndStatusInOrderByIdAsc(
            Long postId, Collection<CommentStatus> statuses);


    long countByPost_IdAndStatus(Long postId, CommentStatus status);

    long countByPost_IdAndStatusIn(Long postId, Collection<CommentStatus> statuses);
}
