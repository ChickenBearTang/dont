package com.ssafy.edu.awesomeproject.domain.auth.controller;

import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.auth.cookie.RefreshTokenCookieService;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.LoginRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.LogoutRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.SignupRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.TokenReissueRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.LoginResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.LogoutResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.TokenReissueResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.service.AuthTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.service.LoginService;
import com.ssafy.edu.awesomeproject.domain.auth.service.SignupService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import java.time.Duration;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private final LoginService loginService;
    private final SignupService signupService;
    private final AuthTokenService authTokenService;
    private final RefreshTokenCookieService refreshTokenCookieService;

    public AuthController(
            LoginService loginService,
            SignupService signupService,
            AuthTokenService authTokenService,
            RefreshTokenCookieService refreshTokenCookieService) {
        this.loginService = loginService;
        this.signupService = signupService;
        this.authTokenService = authTokenService;
        this.refreshTokenCookieService = refreshTokenCookieService;
    }

    @PostMapping("/signup")
    @Operation(summary = "회원가입 API", description = "회원가입 필수 정보 입력을 받아 계정을 생성하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 이메일")
    })
    public CommonResponse<Void> signup(@Valid @RequestBody SignupRequestDto signupRequestDto) {
        signupService.signup(
                signupRequestDto.email(),
                signupRequestDto.password(),
                signupRequestDto.name(),
                signupRequestDto.birthDate(),
                signupRequestDto.nickname(),
                signupRequestDto.termsAgreed(),
                signupRequestDto.cohortId());

        return CommonResponse.success(null);
    }

    @PostMapping("/login")
    @Operation(
            summary = "로그인 API",
            description = "사용자의 이메일과 비밀번호를 받아 로그인 처리 후 사용자 정보를 반환하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패")
    })
    public CommonResponse<LoginResponseDto> login(
            @Valid @RequestBody LoginRequestDto loginRequestDto, HttpServletResponse response) {
        LoginService.LoginResult result =
                loginService.login(loginRequestDto.email(), loginRequestDto.password());

        refreshTokenCookieService.setRefreshToken(
                response,
                result.refreshToken(),
                Duration.ofSeconds(result.refreshTokenExpiresInSeconds()));

        return CommonResponse.success(
                new LoginResponseDto(
                        result.userId(),
                        result.email(),
                        result.userRole(),
                        result.accessToken(),
                        result.tokenType(),
                        result.expiresInSeconds()));
    }

    @PostMapping("/reissue")
    @Operation(summary = "토큰 재발급 API", description = "리프레시 토큰으로 액세스 토큰을 재발급하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "인증 실패")
    })
    public CommonResponse<TokenReissueResponseDto> reissue(
            @RequestBody(required = false) TokenReissueRequestDto tokenReissueRequestDto,
            HttpServletRequest request,
            HttpServletResponse response) {
        String refreshToken =
                refreshTokenCookieService
                        .resolveRefreshToken(request)
                        .orElseGet(
                                () ->
                                        tokenReissueRequestDto == null
                                                ? null
                                                : tokenReissueRequestDto.refreshToken());

        AuthTokenService.ReissueTokenResult result = authTokenService.reissue(refreshToken);

        refreshTokenCookieService.setRefreshToken(
                response,
                result.refreshToken(),
                Duration.ofSeconds(result.refreshTokenExpiresInSeconds()));

        return CommonResponse.success(
                new TokenReissueResponseDto(
                        result.accessToken(), result.tokenType(), result.expiresInSeconds()));
    }

    @PostMapping("/logout")
    @Operation(summary = "로그아웃 API", description = "리프레시 토큰 규약을 검증하여 로그아웃 요청을 처리하는 API입니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
    })
    public CommonResponse<LogoutResponseDto> logout(
            @RequestBody(required = false) LogoutRequestDto logoutRequestDto,
            HttpServletRequest request,
            HttpServletResponse response,
            @RequestHeader(value = "Authorization", required = false) String authorizationHeader) {
        String refreshToken =
                refreshTokenCookieService
                        .resolveRefreshToken(request)
                        .orElseGet(
                                () ->
                                        logoutRequestDto == null
                                                ? null
                                                : logoutRequestDto.refreshToken());

        authTokenService.logout(refreshToken, authorizationHeader);
        refreshTokenCookieService.clearRefreshToken(response);

        return CommonResponse.success(new LogoutResponseDto("Logged out."));
    }
}
