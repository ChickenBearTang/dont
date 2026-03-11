package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

// Board는 (PR, 자유게시판, 기수별 게시판) -> category로 조회
public interface BoardRepository extends JpaRepository<Board,Long> {
    Optional<Board> findByCategory(String category);
}
