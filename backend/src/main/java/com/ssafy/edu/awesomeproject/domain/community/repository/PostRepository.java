package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.jpa.repository.JpaRepository;

import org.springframework.data.domain.Pageable;
import java.util.Optional;

// 게시글 상세 내용
public interface PostRepository extends JpaRepository<Post,Long> {
    Optional<Post> findByIdAndStatus(Long id, PostStatus status);
    Page<Post> findByStatus(PostStatus status, Pageable pageable);
    Page<Post> findByBoard_CategoryAndStatus(BoardCategory category, PostStatus status, Pageable pageable);
}
