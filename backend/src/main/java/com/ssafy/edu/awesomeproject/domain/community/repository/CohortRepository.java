package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface CohortRepository extends JpaRepository<Cohort, Long> {
    interface CohortSummaryProjection {
        Long getCohortId();

        String getCohortCode();
    }

    @Query("select c.id as cohortId, c.cohortCode as cohortCode from Cohort c order by c.generationNo asc")
    List<CohortSummaryProjection> findCohortSummaries();

    Optional<Cohort> findByGenerationNo(Integer generationNo);
}
