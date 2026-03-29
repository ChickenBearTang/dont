package com.ssafy.edu.awesomeproject.domain.fin.account.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.ManualSavingsRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountApiResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.SavingsSettingResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.AccountService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Account", description = "계좌 관리 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/fin/accounts")
public class AccountController {

    private final AccountService accountService;

    @Operation(summary = "[테스트용] 더미 유저 수동 동기화", description = "로그인 불가능한 더미 유저의 잔액을 오픈뱅킹과 강제 동기화하고 랭킹 이벤트를 발생시킵니다.")
    @GetMapping("/test-sync/{userId}")
    public ResponseEntity<AccountApiResponse<String>> testSyncDummy(@PathVariable Long userId) {
        accountService.refreshAccountList(userId);
        boolean published = accountService.forcePublishSaveboxEvent(userId);

        if (published) {
            return ResponseEntity.ok(
                    AccountApiResponse.success("ACC_200_TEST", "더미 유저 강제 동기화 및 랭킹 업데이트를 완료했습니다.", "OK"));
        } else {
            return ResponseEntity.ok(
                    AccountApiResponse.success("ACC_200_TEST_FAIL", "동기화는 성공했으나, 해당 유저의 SAVE_BOX 계좌가 DB에 존재하지 않아 랭킹에 등록되지 않았습니다.", "NO_SAVEBOX"));
        }
    }

    @Operation(summary = "계좌 목록 조회", description = "사용자의 수시입출금 계좌 목록을 조회합니다. (주 계좌 설정용)")
    @GetMapping
    public ResponseEntity<AccountApiResponse<AccountListResponse>> getMyAccounts(
            @CurrentUserId Long userId) {

        AccountListResponse response = accountService.getAccountList(userId);

        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_1", "계좌 목록을 조회했습니다.", response));
    }

    @Operation(summary = "계좌 상세 조회", description = "특정 계좌의 상세 정보를 조회합니다.")
    @GetMapping("/{accountId}")
    public ResponseEntity<AccountApiResponse<AccountResponse>> getAccountDetail(
            @CurrentUserId Long userId, @PathVariable Long accountId) {

        AccountResponse response = accountService.getAccount(userId, accountId);

        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_2", "계좌 상세 정보를 조회했습니다.", response));
    }

    @Operation(summary = "세이브 박스 개설", description = "신규 '세이브 박스' 계좌를 개설합니다. (DB 저장 없음)")
    @PostMapping("/save-box")
    public ResponseEntity<AccountApiResponse<AccountCreateResponse>> createSaveBox(
            @CurrentUserId Long userId, @Valid @RequestBody SaveBoxCreateRequest request) {

        AccountCreateResponse response = accountService.createSaveBox(userId, request);

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(AccountApiResponse.success("SAVEBOX_201_1", "세이브박스가 개설되었습니다.", response));
    }

    @Operation(summary = "계좌 목록 새로고침", description = "외부 API 기준으로 계좌 정보를 재동기화합니다. (DB 업데이트)")
    @PostMapping("/refresh")
    public ResponseEntity<AccountApiResponse<AccountListResponse>> refreshMyAccounts(
            @CurrentUserId Long userId) {

        AccountListResponse response = accountService.refreshAccountList(userId);

        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_3", "계좌 정보가 동기화되었습니다.", response));
    }

    @Operation(summary = "금융 계좌 연동", description = "SSAFY Finance API 키를 등록하고 계좌 정보를 동기화합니다.")
    @PostMapping("/link")
    public ResponseEntity<AccountApiResponse<AccountListResponse>> linkFinanceAccount(
            @CurrentUserId Long userId, @RequestParam String userKey) {

        AccountListResponse response = accountService.linkFinanceAccount(userId, userKey);

        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_9", "금융 계좌가 연동되었습니다.", response));
    }

    @Operation(summary = "주 계좌 설정", description = "특정 계좌를 사용자의 '주 계좌'로 설정합니다.")
    @PatchMapping("/{accountId}/primary")
    public ResponseEntity<AccountApiResponse<AccountResponse>> setPrimaryAccount(
            @CurrentUserId Long userId, @PathVariable Long accountId) {

        AccountResponse response = accountService.setPrimaryAccount(userId, accountId);

        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_4", "주계좌로 설정되었습니다.", response));
    }

    @Operation(summary = "계좌 거래 내역 조회", description = "특정 계좌의 거래 내역을 조회합니다. (자동으로 최신 동기화 시도)")
    @GetMapping("/{accountId}/transactions")
    public ResponseEntity<AccountApiResponse<AccountTransactionResponse>> getAccountTransactions(
            @CurrentUserId Long userId,
            @PathVariable Long accountId,
            @Parameter(description = "조회 시작일 (YYYYMMDD)", example = "20240101")
                    @RequestParam(required = false)
                    String startDate,
            @Parameter(description = "조회 종료일 (YYYYMMDD)", example = "20241231")
                    @RequestParam(required = false)
                    String endDate) {

        AccountTransactionResponse response =
                accountService.getAccountTransactions(userId, accountId, startDate, endDate);

        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_5", "거래 내역을 조회했습니다.", response));
    }

    @Operation(summary = "저축 설정 조회", description = "사용자의 현재 자동 저축 설정을 조회합니다.")
    @GetMapping("/savings-settings")
    public ResponseEntity<AccountApiResponse<SavingsSettingResponse>> getSavingsSetting(
            @CurrentUserId Long userId) {
        SavingsSettingResponse response = accountService.getSavingsSetting(userId);
        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_6", "저축 설정을 조회했습니다.", response));
    }

    @Operation(summary = "저축 설정 생성/수정", description = "자동 저축 규칙을 설정합니다. (키워드 매칭 시 자동 이체)")
    @PostMapping("/savings-settings")
    public ResponseEntity<AccountApiResponse<SavingsSettingResponse>> saveSavingsSetting(
            @CurrentUserId Long userId, @Valid @RequestBody SavingsSettingRequest request) {
        SavingsSettingResponse response =
                accountService.createOrUpdateSavingsSetting(userId, request);
        return ResponseEntity.ok(
                AccountApiResponse.success("ACC_200_7", "저축 설정이 완료되었습니다.", response));
    }

    @Operation(summary = "수동 저축 실행", description = "설정된 주계좌에서 세이브박스로 직접 금액을 이체합니다. (비밀번호 검증 포함)")
    @PostMapping("/manual-savings")
    public ResponseEntity<AccountApiResponse<Void>> manualSavings(
            @CurrentUserId Long userId, @Valid @RequestBody ManualSavingsRequest request) {
        accountService.manualSavings(userId, request.amount(), request.password());
        return ResponseEntity.ok(AccountApiResponse.success("ACC_200_8", "저축 이체가 완료되었습니다.", null));
    }

    @Operation(summary = "수동 출금 실행", description = "세이브박스에서 주계좌로 직접 금액을 꺼냅니다. (비밀번호 검증 포함)")
    @PostMapping("/manual-withdrawal")
    public ResponseEntity<AccountApiResponse<Void>> manualWithdrawal(
            @CurrentUserId Long userId, @Valid @RequestBody ManualSavingsRequest request) {
        accountService.manualWithdrawal(userId, request.amount(), request.password());
        return ResponseEntity.ok(AccountApiResponse.success("ACC_200_10", "출금 이체가 완료되었습니다.", null));
    }
}
