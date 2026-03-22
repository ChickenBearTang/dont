package com.ssafy.edu.awesomeproject.domain.user.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.NicknameChangeRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.MyPageResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.NicknameChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.service.UserProfileService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/users/me")
public class UserProfileController {
    private final UserProfileService userProfileService;

    public UserProfileController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    @GetMapping
    @Operation(summary = "마이페이지 조회 API", description = "현재 로그인한 사용자의 프로필 정보를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<MyPageResponseDto> getMyPage(@CurrentUserId Long userId) {
        return CommonResponse.success(userProfileService.getMyPage(userId));
    }

    @PatchMapping("/nickname")
    @Operation(summary = "닉네임 변경 API", description = "현재 로그인한 사용자의 닉네임을 변경합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음"),
        @ApiResponse(responseCode = "409", description = "이미 사용 중인 닉네임")
    })
    public CommonResponse<NicknameChangeResponseDto> changeNickname(
            @CurrentUserId Long userId, @Valid @RequestBody NicknameChangeRequestDto request) {
        return CommonResponse.success(
                userProfileService.changeNickname(userId, request.nickname()));
    }
}
