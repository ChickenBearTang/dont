package com.ssafy.edu.awesomeproject.domain.fin.account.controller;

import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.SavingsSettingResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.AccountService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
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

    @Operation(summary = "계좌 목록 조회", description = "사용자의 수시입출금 계좌 목록을 조회합니다. (주 계좌 설정용)")
    @GetMapping
    public ResponseEntity<AccountListResponse> getMyAccounts() {

        Long currentUserId = 10L; // (사용자 10번으로 연동)

        AccountListResponse response = accountService.getAccountList(currentUserId);

        return ResponseEntity.ok(response);
    }

    @Operation(summary = "계좌 상세 조회", description = "특정 계좌의 상세 정보를 조회합니다.")
    @GetMapping("/{accountId}")
    public ResponseEntity<AccountResponse> getAccountDetail(@PathVariable Long accountId) {

        Long currentUserId = 10L; // (사용자 10번으로 연동)

        AccountResponse response = accountService.getAccount(currentUserId, accountId);

        return ResponseEntity.ok(response);
    }

    @Operation(summary = "세이브 박스 개설", description = "신규 '세이브 박스' 계좌를 개설합니다. (DB 저장 없음)")
    @PostMapping("/save-box")
    public ResponseEntity<AccountCreateResponse> createSaveBox(
            @RequestBody SaveBoxCreateRequest request) {

        Long currentUserId = 10L; // (사용자 10번으로 연동)

        AccountCreateResponse response = accountService.createSaveBox(currentUserId, request);

        return ResponseEntity.ok(response);
    }

    @Operation(summary = "계좌 목록 새로고침", description = "외부 API 기준으로 계좌 정보를 재동기화합니다. (DB 업데이트)")
    @PostMapping("/refresh")
    public ResponseEntity<AccountListResponse> refreshMyAccounts() {

        Long currentUserId = 10L; // (사용자 10번으로 연동)

        AccountListResponse response = accountService.refreshAccountList(currentUserId);

        return ResponseEntity.ok(response);
    }

    @Operation(summary = "주 계좌 설정", description = "특정 계좌를 사용자의 '주 계좌'로 설정합니다.")
    @PatchMapping("/{accountId}/primary")
    public ResponseEntity<AccountResponse> setPrimaryAccount(@PathVariable Long accountId) {

        Long currentUserId = 10L; // (사용자 10번으로 연동)

        AccountResponse response = accountService.setPrimaryAccount(currentUserId, accountId);

        return ResponseEntity.ok(response);
    }

    @Operation(summary = "계좌 거래 내역 조회", description = "특정 계좌의 거래 내역을 조회합니다. (자동으로 최신 동기화 시도)")
    @GetMapping("/{accountId}/transactions")
    public ResponseEntity<AccountTransactionResponse> getAccountTransactions(
            @PathVariable Long accountId,
            @Parameter(description = "조회 시작일 (YYYYMMDD)", example = "20240101") @RequestParam(defaultValue = "20240101") String startDate,
            @Parameter(description = "조회 종료일 (YYYYMMDD)", example = "20241231") @RequestParam(defaultValue = "20241231") String endDate) {

        Long currentUserId = 10L;

        AccountTransactionResponse response = accountService.getAccountTransactions(currentUserId, accountId, startDate, endDate);

        return ResponseEntity.ok(response);
    }

    @Operation(summary = "저축 설정 조회", description = "사용자의 현재 자동 저축 설정을 조회합니다.")
    @GetMapping("/savings-settings")
    public ResponseEntity<SavingsSettingResponse> getSavingsSetting() {
        Long currentUserId = 10L;
        SavingsSettingResponse response = accountService.getSavingsSetting(currentUserId);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "저축 설정 생성/수정", description = "자동 저축 규칙을 설정합니다. (키워드 매칭 시 자동 이체)")
    @PostMapping("/savings-settings")
    public ResponseEntity<SavingsSettingResponse> saveSavingsSetting(
            @RequestBody SavingsSettingRequest request) {
        Long currentUserId = 10L;
        SavingsSettingResponse response = accountService.createOrUpdateSavingsSetting(currentUserId, request);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "수동 저축 실행", description = "설정된 주계좌에서 세이브박스로 직접 금액을 이체합니다.")
    @PostMapping("/manual-savings")
    public ResponseEntity<Void> manualSavings(@RequestParam java.math.BigDecimal amount) {
        Long currentUserId = 10L;
        accountService.manualSavings(currentUserId, amount);
        return ResponseEntity.ok().build();
    }
}
