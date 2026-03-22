package com.ssafy.edu.awesomeproject.domain.user.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.auth.cookie.RefreshTokenCookieService;
import com.ssafy.edu.awesomeproject.domain.auth.service.AuthTokenService;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.MyPageUpdateRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.NicknameChangeRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.PasswordChangeRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.ProfileImageCompleteRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.ProfileImagePresignRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.WithdrawRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.MyPageResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.NicknameChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.PasswordChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.ProfileImageDeleteResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.ProfileImagePresignResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.ProfileImageResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.WithdrawResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.service.UserProfileService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/users/me")
public class UserProfileController {
    private final UserProfileService userProfileService;
    private final AuthTokenService authTokenService;
    private final RefreshTokenCookieService refreshTokenCookieService;

    public UserProfileController(
            UserProfileService userProfileService,
            AuthTokenService authTokenService,
            RefreshTokenCookieService refreshTokenCookieService) {
        this.userProfileService = userProfileService;
        this.authTokenService = authTokenService;
        this.refreshTokenCookieService = refreshTokenCookieService;
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

    @PatchMapping
    @Operation(summary = "마이페이지 수정 API", description = "현재 로그인한 사용자의 일반 프로필 정보를 수정합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<MyPageResponseDto> updateMyPage(
            @CurrentUserId Long userId, @Valid @RequestBody MyPageUpdateRequestDto request) {
        return CommonResponse.success(userProfileService.updateMyPage(userId, request));
    }

    @PatchMapping("/password")
    @Operation(summary = "비밀번호 변경 API", description = "현재 로그인한 사용자의 비밀번호를 변경합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패 또는 현재 비밀번호 불일치"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<PasswordChangeResponseDto> changePassword(
            @CurrentUserId Long userId,
            @Valid @RequestBody PasswordChangeRequestDto request,
            @RequestHeader(value = "Authorization", required = false) String authorizationHeader,
            HttpServletResponse response) {
        PasswordChangeResponseDto changeResult =
                userProfileService.changePassword(
                        userId, request.currentPassword(), request.newPassword());
        authTokenService.blacklistAccessTokenByAuthorizationHeader(authorizationHeader, userId);
        refreshTokenCookieService.clearRefreshToken(response);
        return CommonResponse.success(changeResult);
    }

    @PostMapping("/profile-image/presign")
    @Operation(
            summary = "프로필 이미지 업로드 URL 발급 API",
            description = "프로필 이미지 업로드용 Presigned URL을 발급합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<ProfileImagePresignResponseDto> createProfileImageUploadUrl(
            @CurrentUserId Long userId, @Valid @RequestBody ProfileImagePresignRequestDto request) {
        return CommonResponse.success(
                userProfileService.createProfileImageUploadUrl(
                        userId,
                        request.fileName(),
                        request.contentType(),
                        request.contentLength()));
    }

    @PatchMapping("/profile-image")
    @Operation(summary = "프로필 이미지 반영 API", description = "업로드 완료된 프로필 이미지 key를 사용자 정보에 반영합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<ProfileImageResponseDto> completeProfileImageUpload(
            @CurrentUserId Long userId,
            @Valid @RequestBody ProfileImageCompleteRequestDto request) {
        return CommonResponse.success(
                userProfileService.completeProfileImageUpload(userId, request.key()));
    }

    @DeleteMapping("/profile-image")
    @Operation(summary = "프로필 이미지 삭제 API", description = "현재 로그인한 사용자의 프로필 이미지를 삭제합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<ProfileImageDeleteResponseDto> deleteProfileImage(
            @CurrentUserId Long userId) {
        return CommonResponse.success(userProfileService.deleteProfileImage(userId));
    }

    @DeleteMapping
    @Operation(summary = "회원 탈퇴 API", description = "현재 로그인한 사용자를 soft delete 처리합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패 또는 현재 비밀번호 불일치"),
        @ApiResponse(responseCode = "404", description = "사용자 없음")
    })
    public CommonResponse<WithdrawResponseDto> withdraw(
            @CurrentUserId Long userId,
            @Valid @RequestBody WithdrawRequestDto request,
            @RequestHeader(value = "Authorization", required = false) String authorizationHeader,
            HttpServletResponse response) {
        WithdrawResponseDto withdrawResult =
                userProfileService.withdraw(userId, request.currentPassword());
        authTokenService.blacklistAccessTokenByAuthorizationHeader(authorizationHeader, userId);
        refreshTokenCookieService.clearRefreshToken(response);
        return CommonResponse.success(withdrawResult);
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
