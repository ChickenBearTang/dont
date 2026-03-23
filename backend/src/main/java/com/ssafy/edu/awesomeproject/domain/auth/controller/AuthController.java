package com.ssafy.edu.awesomeproject.domain.auth.controller;

import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.auth.cookie.RefreshTokenCookieService;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.EmailVerificationConfirmRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.EmailVerificationSendRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.LoginRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.LogoutRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.PasswordResetConfirmRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.PasswordResetRequestRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.SignupRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.request.TokenReissueRequestDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.EmailAvailabilityResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.EmailVerificationConfirmResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.EmailVerificationSendResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.LoginResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.LogoutResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.PasswordResetConfirmResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.PasswordResetRequestResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.dto.response.TokenReissueResponseDto;
import com.ssafy.edu.awesomeproject.domain.auth.service.AccountValidationService;
import com.ssafy.edu.awesomeproject.domain.auth.service.AuthTokenService;
import com.ssafy.edu.awesomeproject.domain.auth.service.EmailVerificationService;
import com.ssafy.edu.awesomeproject.domain.auth.service.LoginService;
import com.ssafy.edu.awesomeproject.domain.auth.service.PasswordResetService;
import com.ssafy.edu.awesomeproject.domain.auth.service.SignupService;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.CohortResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.CohortQueryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import java.time.Duration;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private final LoginService loginService;
    private final SignupService signupService;
    private final PasswordResetService passwordResetService;
    private final AccountValidationService accountValidationService;
    private final CohortQueryService cohortQueryService;
    private final EmailVerificationService emailVerificationService;
    private final AuthTokenService authTokenService;
    private final RefreshTokenCookieService refreshTokenCookieService;

    public AuthController(
            LoginService loginService,
            SignupService signupService,
            PasswordResetService passwordResetService,
            AccountValidationService accountValidationService,
            CohortQueryService cohortQueryService,
            EmailVerificationService emailVerificationService,
            AuthTokenService authTokenService,
            RefreshTokenCookieService refreshTokenCookieService) {
        this.loginService = loginService;
        this.signupService = signupService;
        this.passwordResetService = passwordResetService;
        this.accountValidationService = accountValidationService;
        this.cohortQueryService = cohortQueryService;
        this.emailVerificationService = emailVerificationService;
        this.authTokenService = authTokenService;
        this.refreshTokenCookieService = refreshTokenCookieService;
    }

    @GetMapping("/cohorts")
    @Operation(summary = "기수 목록 조회 API", description = "회원가입 및 온보딩에 필요한 기수 목록을 조회합니다.")
    @ApiResponses({@ApiResponse(responseCode = "200", description = "정상 응답")})
    public CommonResponse<List<CohortResponseDto>> getCohorts() {
        return CommonResponse.success(cohortQueryService.getCohorts());
    }

    @GetMapping("/check-email")
    @Operation(summary = "이메일 중복 확인 API", description = "회원가입 전 이메일 사용 가능 여부를 확인합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public CommonResponse<EmailAvailabilityResponseDto> checkEmail(@RequestParam String email) {
        return CommonResponse.success(accountValidationService.checkEmailAvailability(email));
    }

    @PostMapping("/email-verification/send")
    @Operation(summary = "이메일 인증 코드 발송 API", description = "회원가입용 이메일 인증 코드를 발송합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 이메일"),
        @ApiResponse(responseCode = "502", description = "메일 전송 실패")
    })
    public CommonResponse<EmailVerificationSendResponseDto> sendEmailVerificationCode(
            @Valid @RequestBody EmailVerificationSendRequestDto requestDto) {
        EmailVerificationService.SendResult result =
                emailVerificationService.sendVerificationCode(requestDto.email());

        return CommonResponse.success(
                new EmailVerificationSendResponseDto(result.email(), result.expiresInSeconds()));
    }

    @PostMapping("/email-verification/confirm")
    @Operation(summary = "이메일 인증 코드 검증 API", description = "이메일로 받은 인증 코드를 검증합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 또는 인증 코드 불일치/만료")
    })
    public CommonResponse<EmailVerificationConfirmResponseDto> confirmEmailVerificationCode(
            @Valid @RequestBody EmailVerificationConfirmRequestDto requestDto) {
        EmailVerificationService.VerifyResult result =
                emailVerificationService.verifyCode(requestDto.email(), requestDto.code());

        return CommonResponse.success(
                new EmailVerificationConfirmResponseDto(
                        result.email(), result.verified(), result.verifiedExpiresInSeconds()));
    }

    @PostMapping("/password-reset/request")
    @Operation(summary = "비밀번호 재설정 코드 요청 API", description = "입력한 이메일로 비밀번호 재설정 코드를 전송합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "502", description = "메일 전송 실패")
    })
    public CommonResponse<PasswordResetRequestResponseDto> requestPasswordReset(
            @Valid @RequestBody PasswordResetRequestRequestDto requestDto) {
        PasswordResetService.RequestResult result =
                passwordResetService.requestReset(requestDto.email());
        return CommonResponse.success(
                new PasswordResetRequestResponseDto(result.message(), result.expiresInSeconds()));
    }

    @PostMapping("/password-reset/confirm")
    @Operation(summary = "비밀번호 재설정 확정 API", description = "재설정 코드를 검증하고 비밀번호를 변경합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 또는 코드 오류"),
        @ApiResponse(responseCode = "401", description = "인증 실패")
    })
    public CommonResponse<PasswordResetConfirmResponseDto> confirmPasswordReset(
            @Valid @RequestBody PasswordResetConfirmRequestDto requestDto) {
        PasswordResetService.ConfirmResult result =
                passwordResetService.confirmReset(
                        requestDto.email(), requestDto.code(), requestDto.newPassword());
        return CommonResponse.success(new PasswordResetConfirmResponseDto(result.resetCompleted()));
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
