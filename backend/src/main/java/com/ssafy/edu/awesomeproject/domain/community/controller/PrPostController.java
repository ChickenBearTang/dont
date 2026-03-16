package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.service.AccessTokenService;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCloseRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrVoteSubmitRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCloseResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrVoteSubmitResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.service.PrPostService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/purchase-requests")
public class PrPostController {
    private static final String BEARER_PREFIX = "Bearer ";

    private final PrPostService prPostService;
    private final AccessTokenService accessTokenService;

    public PrPostController(PrPostService prPostService, AccessTokenService accessTokenService) {
        this.prPostService = prPostService;
        this.accessTokenService = accessTokenService;
    }

    @PostMapping
    @ApiCommonResponses
    @Operation(summary = "구매 PR 등록 API", description = "구매 PR을 등록합니다.")
    public CommonResponse<PrCreateResponseDto> createPurchaseRequest(
            @RequestHeader("Authorization") String authorizationHeader,
            @Valid @RequestBody PrCreateRequestDto prCreateRequestDto) {
        Long userId = extractUserIdFromAuthorizationHeader(authorizationHeader);
        return CommonResponse.success(prPostService.create(userId, prCreateRequestDto));
    }

    @GetMapping("/{postId}")
    @ApiCommonResponses
    @Operation(summary = "구매 PR 조회 API", description = "구매 PR을 상세 조회합니다.")
    public CommonResponse<PrDetailResponseDto> getPurchaseRequestDetail(@PathVariable Long postId) {
        return CommonResponse.success(prPostService.detail(postId));
    }

    @PostMapping("/{postId}/votes")
    @ApiCommonResponses
    @Operation(summary = "구매 PR 투표 API", description = "다른 사용자가 올린 PR 내용을 보고 동의하는 지 반대하는 지 투표합니다.")
    public CommonResponse<PrVoteSubmitResponseDto> submitVote(
            @PathVariable Long postId,
            @RequestHeader("Authorization") String authorizationHeader,
            @Valid @RequestBody PrVoteSubmitRequestDto prVoteSubmitRequestDto) {
        Long userId = extractUserIdFromAuthorizationHeader(authorizationHeader);
        return CommonResponse.success(prPostService.vote(postId, userId, prVoteSubmitRequestDto));
    }

    @PostMapping("/{postId}/close")
    @ApiCommonResponses
    @Operation(summary = "구매 PR 닫기 API", description = "작성자가 수동으로 구매 PR을 닫습니다.")
    public CommonResponse<PrCloseResponseDto> closePurchaseRequest(
            @PathVariable Long postId,
            @RequestHeader("Authorization") String authorizationHeader,
            @Valid @RequestBody PrCloseRequestDto prCloseRequestDto) {
        Long userId = extractUserIdFromAuthorizationHeader(authorizationHeader);
        return CommonResponse.success(prPostService.close(postId, userId, prCloseRequestDto));
    }

    private Long extractUserIdFromAuthorizationHeader(String authorizationHeader) {
        String token = extractBearerToken(authorizationHeader);
        ParsedToken parsedToken = accessTokenService.parseAccessToken(token);

        try {
            return Long.parseLong(parsedToken.subject());
        } catch (NumberFormatException exception) {
            throw new CommunityException(CommunityErrorCode.INVALID_INPUT);
        }
    }

    private String extractBearerToken(String authorizationHeader) {
        if (authorizationHeader == null || authorizationHeader.isBlank()) {
            throw new CommunityException(CommunityErrorCode.INVALID_INPUT);
        }

        if (authorizationHeader.startsWith(BEARER_PREFIX)) {
            return authorizationHeader.substring(BEARER_PREFIX.length()).trim();
        }

        return authorizationHeader;
    }
}
