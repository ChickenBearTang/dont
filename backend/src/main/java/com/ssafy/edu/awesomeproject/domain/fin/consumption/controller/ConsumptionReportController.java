package com.ssafy.edu.awesomeproject.domain.fin.consumption.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request.EvaluateJustificationRequest;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request.GenerateMonthlyReportRequest;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.AvgCohort;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.JustificationEvaluationResponse;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.MonthlyReportResponse;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.MonthlyReportGenerationSource;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.service.ConsumptionReportService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("fin/consumption/reports")
public class ConsumptionReportController {

    private final ConsumptionReportService consumptionReportService;


    @PostMapping("/monthly")
    @Operation(summary = "특정 월의 리포트 작성", description = "특정 월의 리포트를 작성합니다.")
    public ResponseEntity<CommonResponse<MonthlyReportResponse>> generateMonthlyReport(
            @CurrentUserId Long userId, @RequestBody @Valid GenerateMonthlyReportRequest request) {

        MonthlyReportResponse response =
                consumptionReportService.generateMonthlyReport(
                        userId, request, MonthlyReportGenerationSource.MANUAL);
        return ResponseEntity.ok(CommonResponse.success(response));
    }


    @GetMapping("/monthly")
    @Operation(summary = "특정 월의 리포트 조회", description = "특정월의 리포트를 조회합니다")
    public ResponseEntity<CommonResponse<MonthlyReportResponse>> getLatestMonthlyReport(
            @CurrentUserId Long userId, @RequestParam String reportMonth) {
        MonthlyReportResponse response =
                consumptionReportService.getLatestMonthlyReport(userId, reportMonth);
        return ResponseEntity.ok(CommonResponse.success(response));
    }


    @PostMapping("/justifications/evaluate")
    @Operation(summary = "반박을 합니다.", description = "리포트에 대해 반박을 수행합니다.")
    public ResponseEntity<CommonResponse<JustificationEvaluationResponse>> evaluateJustification(
            @CurrentUserId Long userId, @RequestBody @Valid EvaluateJustificationRequest request) {
        JustificationEvaluationResponse response =
                consumptionReportService.evaluateAndSaveJustification(
                        userId, request.targetMonth(), request.message());
        return ResponseEntity.ok(CommonResponse.success(response));
    }

    @GetMapping("/compare")
    @Operation(summary = "특정 기수 싸피원들의 지표를 반환합니다." , description = "세이브 박스 평균, 카테고리별 지출액 평균 (금월 1일부터 현재 일 까지)")
    public ResponseEntity<CommonResponse<AvgCohort>> compareToPeer(
        @CurrentUserId Long userId
    ){

        AvgCohort response =
                consumptionReportService.avgCohort(userId);

        return ResponseEntity.ok(CommonResponse.success(response));
    }

}
