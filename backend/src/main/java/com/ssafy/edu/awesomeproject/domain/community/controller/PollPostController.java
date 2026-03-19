package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PollCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PollUpdateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PollVoteSubmitRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollUpdateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollVoteSubmitResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.PollPostService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/polls")
public class PollPostController {
    private final PollPostService pollPostService;

    public PollPostController(PollPostService pollPostService) {
        this.pollPostService = pollPostService;
    }

    @PostMapping
    @ApiCommonResponses
    @Operation(summary = "토론 생성 API", description = "토론 글을 생성합니다.")
    public CommonResponse<PollCreateResponseDto> create(
            @CurrentUserId Long userId,
            @Valid @RequestBody PollCreateRequestDto pollCreateRequestDto) {
        return CommonResponse.success(pollPostService.create(userId, pollCreateRequestDto));
    }

    @GetMapping("/{postId}")
    @ApiCommonResponses
    @Operation(summary = "토론 상세 조회 API", description = "토론 글과 현재 투표 집계를 조회합니다.")
    public CommonResponse<PollDetailResponseDto> detail(@PathVariable Long postId) {
        return CommonResponse.success(pollPostService.detail(postId));
    }

    @PatchMapping("/{postId}")
    @ApiCommonResponses
    @Operation(summary = "토론 수정 API", description = "작성자 본인의 토론 글을 수정합니다.")
    public CommonResponse<PollUpdateResponseDto> update(
            @PathVariable Long postId,
            @CurrentUserId Long userId,
            @Valid @RequestBody PollUpdateRequestDto pollUpdateRequestDto) {
        return CommonResponse.success(pollPostService.update(postId, userId, pollUpdateRequestDto));
    }

    @PostMapping("/{postId}/votes")
    @ApiCommonResponses
    @Operation(summary = "토론 투표 API", description = "A/B 중 하나에 투표하며 기존 투표는 변경 가능합니다.")
    public CommonResponse<PollVoteSubmitResponseDto> vote(
            @PathVariable Long postId,
            @CurrentUserId Long userId,
            @Valid @RequestBody PollVoteSubmitRequestDto pollVoteSubmitRequestDto) {
        return CommonResponse.success(
                pollPostService.vote(postId, userId, pollVoteSubmitRequestDto));
    }
}
