package com.ssafy.edu.awesomeproject.domain.dummy.controller;

import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.request.DummyCreateAccountsRequest;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.request.DummyCreateCardRequest;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.request.DummyCreateUserRequest;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateAccountsResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateCardResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.dto.response.DummyCreateUserResponse;
import com.ssafy.edu.awesomeproject.domain.dummy.service.DummyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/dummy")
public class DummyController {
    private final DummyService dummyService;

    @PostMapping("/creat_user")
    @Operation(
            summary = "더미 사용자 생성 API",
            description = "기수를 입력받아 더미 사용자를 생성하고 SSAFY 금융 userKey를 발급/저장합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "404", description = "기수를 찾을 수 없음"),
        @ApiResponse(responseCode = "409", description = "외부 userKey 중복"),
        @ApiResponse(responseCode = "500", description = "외부 API 응답 오류")
    })
    public CommonResponse<DummyCreateUserResponse> createUser(
            @Valid @RequestBody DummyCreateUserRequest request) {
        return CommonResponse.success(dummyService.createDummyUser(request.generationNo()));
    }

    @PostMapping("/create_accounts")
    @Operation(
            summary = "더미 사용자 계좌 생성 API",
            description = "userId를 입력받아 세이브박스 1개와 주거래통장 1개를 생성하고 주계좌로 설정합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "404", description = "사용자를 찾을 수 없음"),
        @ApiResponse(responseCode = "500", description = "외부 API 응답 오류")
    })
    public CommonResponse<DummyCreateAccountsResponse> createAccounts(
            @Valid @RequestBody DummyCreateAccountsRequest request) {
        return CommonResponse.success(dummyService.createDummyAccounts(request.userId()));
    }

    @PostMapping("/create_card")
    @Operation(
            summary = "더미 사용자 카드 생성 API",
            description = "userId를 입력받아 주거래통장 자동이체 기준으로 카드 1장을 생성하고 DB를 동기화합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "정상 응답"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "404", description = "사용자를 찾을 수 없음"),
        @ApiResponse(responseCode = "500", description = "외부 API 응답 오류")
    })
    public CommonResponse<DummyCreateCardResponse> createCard(
            @Valid @RequestBody DummyCreateCardRequest request) {
        return CommonResponse.success(dummyService.createDummyCard(request.userId()));
    }
}
