package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.PrXaiEvaluationService;
import io.swagger.v3.oas.annotations.Operation;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/purchase-requests")
public class PrXaiEvaluationController {

    private final PrXaiEvaluationService prXaiEvaluationService;

    public PrXaiEvaluationController(PrXaiEvaluationService prXaiEvaluationService) {
        this.prXaiEvaluationService = prXaiEvaluationService;
    }

    @GetMapping("/{postId}/xai-evaluation")
    @ApiCommonResponses
    @Operation(summary = "구매 PR XAI 평가 조회", description = "구매 PR에 대한 XAI 평가 결과를 조회합니다.")
    public CommonResponse<PrXaiEvaluationResponseDto> getXaiEvaluation(
            @PathVariable Long postId, @CurrentUserId Long userId) {
        return CommonResponse.success(prXaiEvaluationService.evaluate(postId, userId));
    }
}
