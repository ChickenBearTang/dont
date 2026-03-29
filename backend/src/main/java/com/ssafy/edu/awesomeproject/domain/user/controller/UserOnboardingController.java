package com.ssafy.edu.awesomeproject.domain.user.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.OnboardingCheckpointRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.OnboardingStatusResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.service.UserOnboardingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/users/onboarding")
public class UserOnboardingController {
    private final UserOnboardingService userOnboardingService;

    public UserOnboardingController(UserOnboardingService userOnboardingService) {
        this.userOnboardingService = userOnboardingService;
    }

    @GetMapping("/status")
    @Operation(summary = "온보딩 상태 조회 API", description = "현재 로그인한 사용자의 온보딩 완료 여부를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<OnboardingStatusResponseDto> getOnboardingStatus(
            @CurrentUserId Long userId) {
        return CommonResponse.success(userOnboardingService.getOnboardingStatus(userId));
    }

    @PostMapping
    @Operation(
            summary = "온보딩 체크포인트 저장 API",
            description = "추천 저축액을 임시 저장하고 온보딩 상태를 IN_PROGRESS로 전환합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<OnboardingStatusResponseDto> saveOnboardingCheckpoint(
            @CurrentUserId Long userId,
            @Valid @RequestBody OnboardingCheckpointRequestDto request) {
        return CommonResponse.success(
                userOnboardingService.saveOnboardingCheckpoint(
                        userId, request.recommendedAmount()));
    }

    @PostMapping("/complete")
    @Operation(summary = "온보딩 완료 처리 API", description = "현재 로그인한 사용자의 온보딩 상태를 COMPLETED로 변경합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<OnboardingStatusResponseDto> completeOnboarding(
            @CurrentUserId Long userId) {
        return CommonResponse.success(userOnboardingService.completeOnboarding(userId));
    }

    @org.springframework.web.bind.annotation.DeleteMapping
    @Operation(summary = "온보딩 정보 초기화 API", description = "현재 로그인한 사용자의 온보딩 정보와 저축 설정을 초기화합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<Void> resetOnboarding(@CurrentUserId Long userId) {
        userOnboardingService.resetOnboarding(userId);
        return CommonResponse.success(null);
    }
}
