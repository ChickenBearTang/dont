package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.GetCohortResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.CohortService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/cohorts")
public class CohortController {
    private final CohortService cohortService;

    public CohortController(CohortService cohortService) {
        this.cohortService = cohortService;
    }

    @GetMapping
    @Operation(summary = "기수 목록 조회 API", description = "회원가입 및 온보딩에서 사용하는 기수 목록을 조회하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
    })
    public CommonResponse<List<GetCohortResponseDto>> getCohorts() {
        return CommonResponse.success(cohortService.getCohorts());
    }
}
