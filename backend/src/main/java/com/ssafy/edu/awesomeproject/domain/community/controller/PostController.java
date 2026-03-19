package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.CreatePostRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.UpdatePostRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.*;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.service.PostService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController

// 게시글 생성
@RequestMapping("/community/posts")
public class PostController {
    private final PostService postService;

    public PostController(PostService postService) {
        this.postService = postService;
    }

    @PostMapping
    @Operation(
            summary = "게시글 작성 API",
            description = "게시판 카테고리, 기수(cohortId), 제목, 본문을 받아 게시글을 생성하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "생성 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "403", description = "접근 거부")
    })
    public CommonResponse<CreatePostResponseDto> createPost(
            @CurrentUserId Long userId,
            @Valid @RequestBody CreatePostRequestDto createPostRequestDto) {
        PostService.CreatePostResult result =
                postService.createPost(
                        userId,
                        createPostRequestDto.category(),
                        createPostRequestDto.generationNo(),
                        createPostRequestDto.title(),
                        createPostRequestDto.content());

        return CommonResponse.success(
                new CreatePostResponseDto(
                        result.postId(),
                        result.category(),
                        result.generationNo(),
                        result.createdAt()));
    }

    // 게시글 목록조회
    @GetMapping
    @Operation(
            summary = "게시글 목록 조회 API",
            description =
                    "category가 없으면 전체 목록, 있으면 카테고리별 게시글 목록을 페이지 번호 방식으로 조회합니다. COHORT 카테고리 조회 시에는 cohortId를 함께 보내야 합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public CommonResponse<GetPostListResponseDto> getPosts(
            @CurrentUserId Long userId,
            @RequestParam(required = false) BoardCategory category,
            @RequestParam(required = false) Integer generationNo,
            @RequestParam(defaultValue = "0") Integer page,
            @RequestParam(defaultValue = "5") Integer size) {

        PostService.GetPostListResult result =
                postService.getPostsByCategory(userId, category, generationNo, page, size);

        List<GetPostListResponseDto.PostSummaryDto> content =
                result.content().stream()
                        .map(
                                post -> {
                                    PostService.PostExtraSummary extra = post.extraSummary();
                                    return new GetPostListResponseDto.PostSummaryDto(
                                            post.postId(),
                                            post.category(),
                                            post.generationNo(),
                                            post.title(),
                                            post.authorId(),
                                            post.authorNickname(),
                                            post.isMine(),
                                            post.likeCount(),
                                            post.commentCount(),
                                            post.createdAt(),
                                            extra == null
                                                    ? null
                                                    : new GetPostListResponseDto
                                                            .PostExtraSummaryDto(
                                                            extra.pr() == null
                                                                    ? null
                                                                    : new GetPostListResponseDto
                                                                            .PrSummaryDto(
                                                                            extra.pr().status(),
                                                                            extra.pr()
                                                                                    .resultStatus(),
                                                                            extra.pr()
                                                                                    .totalVoteCount(),
                                                                            extra.pr()
                                                                                    .deadlineAt()),
                                                            extra.hotdeal() == null
                                                                    ? null
                                                                    : new GetPostListResponseDto
                                                                            .HotdealSummaryDto(
                                                                            extra.hotdeal()
                                                                                    .dealPriceAmount(),
                                                                            extra.hotdeal()
                                                                                    .originalPriceAmount(),
                                                                            extra.hotdeal()
                                                                                    .storeName(),
                                                                            extra.hotdeal()
                                                                                    .expiredAt(),
                                                                            extra.hotdeal()
                                                                                    .isExpired()),
                                                            extra.poll() == null
                                                                    ? null
                                                                    : new GetPostListResponseDto
                                                                            .PollSummaryDto(
                                                                            extra.poll().question(),
                                                                            extra.poll().optionA(),
                                                                            extra.poll().optionB(),
                                                                            extra.poll()
                                                                                    .deadlineAt(),
                                                                            extra.poll().isClosed(),
                                                                            extra.poll()
                                                                                    .optionACount(),
                                                                            extra.poll()
                                                                                    .optionBCount(),
                                                                            extra.poll()
                                                                                    .totalVoteCount())));
                                })
                        .toList();

        return CommonResponse.success(
                new GetPostListResponseDto(
                        content,
                        result.page(),
                        result.size(),
                        result.totalElements(),
                        result.totalPages(),
                        result.hasNext()));
    }

    // 게시글 상세조회
    @GetMapping("/{postId}")
    @Operation(summary = "게시글 상세 조회 API", description = "게시글 ID로 게시글 상세 정보를 조회하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "404", description = "게시글 없음")
    })
    public CommonResponse<GetPostResponseDto> getPost(
            @CurrentUserId Long userId, @PathVariable Long postId) {

        PostService.GetPostResult result = postService.getPost(userId, postId);

        return CommonResponse.success(
                new GetPostResponseDto(
                        result.postId(),
                        result.category(),
                        result.generationNo(),
                        result.title(),
                        result.content(),
                        result.authorId(),
                        result.authorNickname(),
                        result.isMine(),
                        result.likeCount(),
                        result.dislikeCount(),
                        result.commentCount(),
                        result.createdAt(),
                        result.updatedAt()));
    }

    // 게시글 수정
    @PatchMapping("/{postId}")
    @Operation(summary = "게시글 수정 API", description = "게시글 작성자가 제목과 본문을 수정하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "게시글 없음")
    })
    public CommonResponse<UpdatePostResponseDto> updatePost(
            @CurrentUserId Long userId,
            @PathVariable Long postId,
            @Valid @RequestBody UpdatePostRequestDto updatePostRequestDto) {
        PostService.UpdatePostResult result =
                postService.updatePost(
                        userId,
                        postId,
                        updatePostRequestDto.title(),
                        updatePostRequestDto.content());

        return CommonResponse.success(
                new UpdatePostResponseDto(result.postId(), result.updatedAt()));
    }

    // 게시글 삭제
    @DeleteMapping("/{postId}")
    @Operation(summary = "게시글 삭제 API", description = "게시글 작성자가 게시글을 삭제하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "게시글 없음")
    })
    public CommonResponse<DeletePostResponseDto> deletePost(
            @CurrentUserId Long userId, @PathVariable Long postId) {
        PostService.DeletePostResult result = postService.deletePost(userId, postId);

        return CommonResponse.success(
                new DeletePostResponseDto(result.deleted(), result.deletedAt()));
    }
}
