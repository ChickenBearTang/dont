package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

// 게시글 상세 내용
public interface PostRepository extends JpaRepository<Post,Long> {
    Optional<Post> findByIdAndStatus(Long id, PostStatus status);
}
