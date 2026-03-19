package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface BoardRepository extends JpaRepository<Board, Long> {
    Optional<Board> findByCategory(BoardCategory category);

    Optional<Board> findByCategoryAndCohort_GenerationNo(BoardCategory category, Integer generationNo);

    @Query("""
            select b.id
            from Board b
            left join b.cohort c
            where b.category <> :cohortCategory
               or (c is not null and c.generationNo = :generationNo)
            """)
    List<Long> findVisibleBoardIdsForUser(
            @Param("cohortCategory") BoardCategory cohortCategory,
            @Param("generationNo") Integer generationNo);
}
