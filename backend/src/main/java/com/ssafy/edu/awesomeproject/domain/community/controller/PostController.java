package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.CreatePostRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.UpdatePostRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.*;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.service.PostService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController

//게시글 생성
@RequestMapping("/community/posts")
public class PostController {
    private final PostService postService;
    private final AccessTokenService accessTokenService;

    public PostController(
        PostService postService,
        AccessTokenService accessTokenService) {
        this.postService = postService;
        this.accessTokenService = accessTokenService;
    }

    @PostMapping
    @Operation(
        summary = "게시글 작성 API",
        description = "게시판 카테고리, 기수(cohortId), 제목, 본문을 받아 게시글을 생성하는 API입니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "생성 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "403", description = "접근 거부")
    })
    public CommonResponse<CreatePostResponseDto> createPost(
        @RequestHeader("Authorization") String authorizationHeader,
        @Valid @RequestBody CreatePostRequestDto createPostRequestDto
    ) {

        Long userId = extractUserIdFromAuthorizationHeader(authorizationHeader);

        PostService.CreatePostResult result = postService.createPost(
            userId,
            createPostRequestDto.category(),
            createPostRequestDto.cohortId(),
            createPostRequestDto.title(),
            createPostRequestDto.content()
        );

        return CommonResponse.success(
            new CreatePostResponseDto(
                result.postId(),
                result.category(),
                result.cohortId(),
                result.createdAt()
            )
        );
    }

    //게시글 목록조회
    @GetMapping
    @Operation(
        summary = "게시글 목록 조회 API",
        description = "category가 없으면 전체 목록, 있으면 카테고리별 게시글 목록을 페이지 번호 방식으로 조회합니다. COHORT 카테고리 조회 시에는 cohortId를 함께 보내야 합니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public CommonResponse<GetPostListResponseDto> getPosts(
        @RequestParam(required = false) BoardCategory category,
        @RequestParam(required = false) Long cohortId,
        @RequestParam(defaultValue = "0") Integer page,
        @RequestParam(defaultValue = "5") Integer size
    ) {
        PostService.GetPostListResult result =
            postService.getPostsByCategory(category, cohortId, page, size);

        List<GetPostListResponseDto.PostSummaryDto> content = result.content().stream()
            .map(post -> new GetPostListResponseDto.PostSummaryDto(
                post.postId(),
                post.category(),
                post.cohortId(),
                post.title(),
                post.authorNickname(),
                post.likeCount(),
                post.commentCount(),
                post.createdAt()
            ))
            .toList();

        return CommonResponse.success(
            new GetPostListResponseDto(
                content,
                result.page(),
                result.size(),
                result.totalElements(),
                result.totalPages(),
                result.hasNext()
            )
        );
    }

    //게시글 상세조회
    @GetMapping("/{postId}")
    @Operation(
        summary = "게시글 상세 조회 API",
        description = "게시글 ID로 게시글 상세 정보를 조회하는 API입니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "404", description = "게시글 없음")
    })
    public CommonResponse<GetPostResponseDto> getPost(@PathVariable Long postId) {
        PostService.GetPostResult result = postService.getPost(postId);

        return CommonResponse.success(
            new GetPostResponseDto(
                result.postId(),
                result.category(),
                result.cohortId(),
                result.title(),
                result.content(),
                result.authorNickname(),
                result.likeCount(),
                result.dislikeCount(),
                result.commentCount(),
                result.createdAt(),
                result.updatedAt()
            )
        );
    }

    //게시글 수정
    @PatchMapping("/{postId}")
    @Operation(
        summary = "게시글 수정 API",
        description = "게시글 작성자가 제목과 본문을 수정하는 API입니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "게시글 없음")
    })
    public CommonResponse<UpdatePostResponseDto> updatePost(
        @RequestHeader("Authorization") String authorizationHeader,
        @PathVariable Long postId,
        @Valid @RequestBody UpdatePostRequestDto updatePostRequestDto
    ) {

        Long userId = extractUserIdFromAuthorizationHeader(authorizationHeader);

        PostService.UpdatePostResult result = postService.updatePost(
            userId,
            postId,
            updatePostRequestDto.title(),
            updatePostRequestDto.content()
        );

        return CommonResponse.success(
            new UpdatePostResponseDto(
                result.postId(),
                result.updatedAt()
            )
        );
    }

    //게시글 삭제
    @DeleteMapping("/{postId}")
    @Operation(
        summary = "게시글 삭제 API",
        description = "게시글 작성자가 게시글을 삭제하는 API입니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "403", description = "권한 없음"),
        @ApiResponse(responseCode = "404", description = "게시글 없음")
    })
    public CommonResponse<DeletePostResponseDto> deletePost(
        @RequestHeader("Authorization") String authorizationHeader,
        @PathVariable Long postId
    ) {

        Long userId = extractUserIdFromAuthorizationHeader(authorizationHeader);

        PostService.DeletePostResult result = postService.deletePost(userId, postId);

        return CommonResponse.success(
            new DeletePostResponseDto(
                result.deleted(),
                result.deletedAt()
            )
        );
    }

    private Long extractUserIdFromAuthorizationHeader(String authorizationHeader) {
        String token = extractBearerToken(authorizationHeader);
        ParsedToken parsedToken = accessTokenService.parseAccessToken(token);
        return Long.parseLong(parsedToken.subject());
    }

    private String extractBearerToken(String authorizationHeader) {
        if (authorizationHeader == null || authorizationHeader.isBlank()) {
            throw new IllegalArgumentException("Authorization header is required");
        }

        if (authorizationHeader.startsWith("Bearer ")) {
            return authorizationHeader.substring(7);
        }

        return authorizationHeader;
    }
}
