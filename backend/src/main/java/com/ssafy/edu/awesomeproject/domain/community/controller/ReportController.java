package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.ReportCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.ReportCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/reports")
public class ReportController {
    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    @PostMapping
    @ApiCommonResponses
    @Operation(summary = "신고 생성 API", description = "게시글/댓글을 신고합니다.")
    public CommonResponse<ReportCreateResponseDto> create(
            @CurrentUserId Long userId, @Valid @RequestBody ReportCreateRequestDto requestDto) {
        return CommonResponse.success(reportService.create(userId, requestDto));
    }
}
