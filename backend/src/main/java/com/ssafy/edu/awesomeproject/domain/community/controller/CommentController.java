package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.CreateCommentRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.UpdateCommentRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.CreateCommentResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.DeleteCommentResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.GetCommentListResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.UpdateCommentResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.CommentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community")
public class CommentController {
    private final CommentService commentService;

    public CommentController(CommentService commentService) {
        this.commentService = commentService;
    }

    @PostMapping("/posts/{postId}/comments")
    @Operation(summary = "댓글 작성 API", description = "게시글에 댓글 또는 대댓글을 작성하는 API 입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "생성 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "게시글/댓글 없음")
    })
    public CommonResponse<CreateCommentResponseDto> createComment(
            @CurrentUserId Long userId,
            @PathVariable Long postId,
            @Valid @RequestBody CreateCommentRequestDto createCommentRequestDto) {

        CommentService.CreateCommentResult result =
                commentService.createComment(
                        userId,
                        postId,
                        createCommentRequestDto.parentCommentId(),
                        createCommentRequestDto.content());

        return CommonResponse.success(
                new CreateCommentResponseDto(result.commentId(), result.createdAt()));
    }

    @GetMapping("/posts/{postId}/comments")
    @Operation(summary = "댓글 목록 조회 API", description = "게시글의 댓글 목록을 페이지 기반으로 조회하는 API 입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "404", description = "게시글 없음")
    })
    public CommonResponse<GetCommentListResponseDto> getComments(
            @CurrentUserId Long userId,
            @PathVariable Long postId,
            @RequestParam(required = false) Integer page,
            @RequestParam(required = false) Integer size) {

        CommentService.GetCommentListResult result =
                commentService.getComments(userId, postId, page, size);

        List<GetCommentListResponseDto.CommentSummaryDto> content =
                result.content().stream()
                        .map(
                                comment ->
                                        new GetCommentListResponseDto.CommentSummaryDto(
                                                comment.commentId(),
                                                comment.parentCommentId(),
                                                comment.content(),
                                                comment.authorId(),
                                                comment.authorNickname(),
                                                comment.isMine(),
                                                comment.likeCount(),
                                                comment.createdAt()))
                        .toList();

        return CommonResponse.success(
                new GetCommentListResponseDto(
                        content,
                        result.page(),
                        result.size(),
                        result.totalElements(),
                        result.totalPages(),
                        result.hasNext()));
    }

    @PatchMapping("/comments/{commentId}")
    @Operation(summary = "댓글 수정 API", description = "댓글 작성자가 본인 댓글을 수정하는 API 입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "댓글 없음")
    })
    public CommonResponse<UpdateCommentResponseDto> updateComment(
            @CurrentUserId Long userId,
            @PathVariable Long commentId,
            @Valid @RequestBody UpdateCommentRequestDto updateCommentRequestDto) {

        CommentService.UpdateCommentResult result =
                commentService.updateComment(userId, commentId, updateCommentRequestDto.content());

        return CommonResponse.success(
                new UpdateCommentResponseDto(result.commentId(), result.updatedAt()));
    }

    @DeleteMapping("/comments/{commentId}")
    @Operation(summary = "댓글 삭제 API", description = "댓글 작성자가 본인의 댓글을 삭제하는 API 입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "댓글 없음")
    })
    public CommonResponse<DeleteCommentResponseDto> deleteComment(
            @CurrentUserId Long userId, @PathVariable Long commentId) {

        CommentService.DeleteCommentResult result = commentService.deleteComment(userId, commentId);

        return CommonResponse.success(
                new DeleteCommentResponseDto(result.deleted(), result.deletedAt()));
    }
}
