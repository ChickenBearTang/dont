package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCloseRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrVoteSubmitRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCloseResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrVoteSubmitResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.PrPostService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/purchase-requests")
public class PrPostController {
    private final PrPostService prPostService;

    public PrPostController(PrPostService prPostService) {
        this.prPostService = prPostService;
    }

    @PostMapping
    @ApiCommonResponses
    @Operation(summary = "구매 PR 등록 API", description = "구매 PR을 등록합니다.")
    public CommonResponse<PrCreateResponseDto> createPurchaseRequest(
            @CurrentUserId Long userId, @Valid @RequestBody PrCreateRequestDto prCreateRequestDto) {
        return CommonResponse.success(prPostService.create(userId, prCreateRequestDto));
    }

    @GetMapping("/{postId}")
    @ApiCommonResponses
    @Operation(summary = "구매 PR 조회 API", description = "구매 PR 상세를 조회합니다.")
    public CommonResponse<PrDetailResponseDto> getPurchaseRequestDetail(
            @PathVariable Long postId, @CurrentUserId Long userId) {
        return CommonResponse.success(prPostService.detail(postId, userId));
    }

    @PostMapping("/{postId}/votes")
    @ApiCommonResponses
    @Operation(summary = "구매 PR 투표 API", description = "구매 PR에 찬성/반대 투표를 등록합니다.")
    public CommonResponse<PrVoteSubmitResponseDto> submitVote(
            @PathVariable Long postId,
            @CurrentUserId Long userId,
            @Valid @RequestBody PrVoteSubmitRequestDto prVoteSubmitRequestDto) {
        return CommonResponse.success(prPostService.vote(postId, userId, prVoteSubmitRequestDto));
    }

    @PostMapping("/{postId}/close")
    @ApiCommonResponses
    @Operation(summary = "구매 PR 종료 API", description = "작성자가 수동으로 구매 PR을 종료합니다.")
    public CommonResponse<PrCloseResponseDto> closePurchaseRequest(
            @PathVariable Long postId,
            @CurrentUserId Long userId,
            @Valid @RequestBody PrCloseRequestDto prCloseRequestDto) {
        return CommonResponse.success(prPostService.close(postId, userId, prCloseRequestDto));
    }
}
