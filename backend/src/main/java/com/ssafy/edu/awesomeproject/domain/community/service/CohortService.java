package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.community.dto.response.GetCohortResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class CohortService {
    private final CohortRepository cohortRepository;

    public CohortService(CohortRepository cohortRepository) {
        this.cohortRepository = cohortRepository;
    }

    public List<GetCohortResponseDto> getCohorts() {
        return cohortRepository.findCohortSummaries().stream()
                .map(cohort -> new GetCohortResponseDto(cohort.getCohortId(), cohort.getCohortCode()))
                .toList();
    }
}
