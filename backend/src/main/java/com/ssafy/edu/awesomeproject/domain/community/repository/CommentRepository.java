package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Comment;
import com.ssafy.edu.awesomeproject.domain.community.entity.CommentStatus;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CommentRepository extends JpaRepository<Comment, Long> {
    Optional<Comment> findByIdAndStatus(Long id, CommentStatus status);

    // 목록 조회
    Page<Comment> findByPost_IdAndStatus(Long postId, CommentStatus status, Pageable pageable);

    // 댓글 목록 좋아요 count
    long countByPost_IdAndStatus(Long postId, CommentStatus status);
}
