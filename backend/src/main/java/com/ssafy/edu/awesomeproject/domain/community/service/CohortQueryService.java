package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.community.dto.response.CohortResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class CohortQueryService {
    private final CohortRepository cohortRepository;

    public CohortQueryService(CohortRepository cohortRepository) {
        this.cohortRepository = cohortRepository;
    }

    public List<CohortResponseDto> getCohorts() {
        return cohortRepository.findAllByOrderByGenerationNoAsc().stream()
                .map(
                        cohort ->
                                new CohortResponseDto(
                                        cohort.getId(),
                                        cohort.getCohortCode(),
                                        cohort.getGenerationNo()))
                .toList();
    }
}
