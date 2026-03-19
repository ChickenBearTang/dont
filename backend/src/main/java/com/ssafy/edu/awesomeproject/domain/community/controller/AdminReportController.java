package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.AdminOnly;
import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.ReportProcessRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.AdminReportDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.AdminReportListResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.ReportProcessResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReportStatus;
import com.ssafy.edu.awesomeproject.domain.community.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@AdminOnly
@RestController
@RequestMapping("/admin/reports")
public class AdminReportController {
    private final ReportService reportService;

    public AdminReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    @GetMapping
    @ApiCommonResponses
    @Operation(summary = "신고 목록 조회 API(관리자)", description = "신고 목록을 상태별/페이지별로 조회합니다.")
    public CommonResponse<AdminReportListResponseDto> list(
            @RequestParam(required = false) ReportStatus status,
            @RequestParam(defaultValue = "0") Integer page,
            @RequestParam(defaultValue = "20") Integer size) {
        return CommonResponse.success(reportService.getReportsForAdmin(status, page, size));
    }

    @GetMapping("/{reportId}")
    @ApiCommonResponses
    @Operation(summary = "신고 상세 조회 API(관리자)", description = "단일 신고 상세 정보를 조회합니다.")
    public CommonResponse<AdminReportDetailResponseDto> detail(@PathVariable Long reportId) {
        return CommonResponse.success(reportService.getReportDetailForAdmin(reportId));
    }

    @PatchMapping("/{reportId}/blind")
    @ApiCommonResponses
    @Operation(summary = "신고 블라인드 처리 API(관리자)", description = "신고를 블라인드 상태로 처리합니다.")
    public CommonResponse<ReportProcessResponseDto> blind(
            @PathVariable Long reportId,
            @CurrentUserId Long adminUserId,
            @Valid @RequestBody ReportProcessRequestDto requestDto) {
        return CommonResponse.success(reportService.blind(reportId, adminUserId, requestDto));
    }

    @PatchMapping("/{reportId}/reject")
    @ApiCommonResponses
    @Operation(summary = "신고 기각 처리 API(관리자)", description = "신고를 기각 상태로 처리합니다.")
    public CommonResponse<ReportProcessResponseDto> reject(
            @PathVariable Long reportId,
            @CurrentUserId Long adminUserId,
            @Valid @RequestBody ReportProcessRequestDto requestDto) {
        return CommonResponse.success(reportService.reject(reportId, adminUserId, requestDto));
    }
}
