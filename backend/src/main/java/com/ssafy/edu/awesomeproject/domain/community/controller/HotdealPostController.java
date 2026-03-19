package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.HotdealCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.HotdealUpdateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.HotdealCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.HotdealDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.HotdealUpdateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.HotdealPostService;
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
@RequestMapping("/community/hotdeals")
public class HotdealPostController {
    private final HotdealPostService hotdealPostService;

    public HotdealPostController(HotdealPostService hotdealPostService) {
        this.hotdealPostService = hotdealPostService;
    }

    @PostMapping
    @ApiCommonResponses
    @Operation(summary = "핫딜 등록 API", description = "상품의 정보를 바탕으로 해서 핫딜을 생성합니다.")
    public CommonResponse<HotdealCreateResponseDto> create(
            @CurrentUserId Long userId,
            @Valid @RequestBody HotdealCreateRequestDto hotdealCreateRequestDto) {
        return CommonResponse.success(hotdealPostService.create(userId, hotdealCreateRequestDto));
    }

    @GetMapping("/{postId}")
    @ApiCommonResponses
    @Operation(summary = "핫딜 상세 조회 API", description = "게시글 ID로 핫딜 정보를 조회합니다.")
    public CommonResponse<HotdealDetailResponseDto> detail(@PathVariable Long postId) {
        return CommonResponse.success(hotdealPostService.detail(postId));
    }

    @PatchMapping("/{postId}")
    @ApiCommonResponses
    @Operation(summary = "핫딜 수정 API", description = "작성자 ID로 핫딜 정보를 수정합니다.")
    public CommonResponse<HotdealUpdateResponseDto> update(
            @PathVariable Long postId,
            @CurrentUserId Long userId,
            @Valid @RequestBody HotdealUpdateRequestDto hotdealUpdateRequestDto) {
        Long userId = extractUserIdFromAuthorizationHeader(authorizationHeader);
        return CommonResponse.success(
                hotdealPostService.update(postId, userId, hotdealUpdateRequestDto));
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
