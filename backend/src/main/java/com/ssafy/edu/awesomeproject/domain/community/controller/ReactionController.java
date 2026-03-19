package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.ToggleReactionRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.ToggleReactionResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.ReactionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/reactions")
public class ReactionController {
    private final ReactionService reactionService;

    public ReactionController(ReactionService reactionService) {
        this.reactionService = reactionService;
    }

    @PostMapping
    @Operation(
            summary = "반응 등록 또는 취소 API",
            description = "게시글 또는 댓글에 대해 좋아요/싫어요 반응을 등록하거나 취소하는 API 입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "게시글/댓글 없음"),
        @ApiResponse(responseCode = "409", description = "이미 반응한 대상")
    })
    public CommonResponse<ToggleReactionResponseDto> toggleReaction(
            @CurrentUserId Long userId,
            @Valid @RequestBody ToggleReactionRequestDto toggleReactionRequestDto) {

        ReactionService.ToggleReactionResult result =
                reactionService.toggleReaction(
                        userId,
                        toggleReactionRequestDto.targetType(), // POST, COMMENT
                        toggleReactionRequestDto.targetId(), // postId
                        toggleReactionRequestDto.reactionType(), // LIKE, DISLIKE
                        toggleReactionRequestDto.active()); // true, false (등록, 취소)

        return CommonResponse.success(
                new ToggleReactionResponseDto(
                        result.targetType(),
                        result.targetId(),
                        result.reactionType(),
                        result.active(),
                        result.likeCount(),
                        result.dislikeCount()));
    }
}
