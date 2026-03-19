package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Comment;
import com.ssafy.edu.awesomeproject.domain.community.entity.CommentStatus;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CommentRepository extends JpaRepository<Comment, Long> {
    Optional<Comment> findByIdAndStatus(Long id, CommentStatus status);

    // 목록 조회
    @EntityGraph(attributePaths = {"user", "parentComment"})
    Page<Comment> findByPost_IdAndStatus(Long postId, CommentStatus status, Pageable pageable);

    //댓글 목록 좋아요 count
    long countByPost_IdAndStatus(Long postId, CommentStatus status);

    @Query("""
            select c.post.id as postId, count(c) as commentCount
            from Comment c
            where c.status = :status
              and c.post.id in :postIds
            group by c.post.id
            """)
    List<PostCommentCountProjection> aggregateCountByPostIdsAndStatus(
            @Param("postIds") Collection<Long> postIds,
            @Param("status") CommentStatus status);

    interface PostCommentCountProjection {
        Long getPostId();

        Long getCommentCount();
    }
}
