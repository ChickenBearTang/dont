package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;


public interface BoardRepository extends JpaRepository<Board, Long> {
    Optional<Board> findByCategory(BoardCategory category);


    Optional<Board> findByCategoryAndCohort_GenerationNo(
            BoardCategory category, Integer generationNo);
}
