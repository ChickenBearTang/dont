package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

// Board는 (PR, 자유게시판, 기수별 게시판) -> enum boardCategory로 조회
public interface BoardRepository extends JpaRepository<Board, Long> {
    Optional<Board> findByCategory(BoardCategory category);

    // category = cohort 일 때 cohort_id 별로 기수 게시판 조회
    Optional<Board> findByCategoryAndCohort_GenerationNo(
            BoardCategory category, Integer generationNo);
}
