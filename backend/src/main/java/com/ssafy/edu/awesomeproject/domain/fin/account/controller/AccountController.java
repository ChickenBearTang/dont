package com.ssafy.edu.awesomeproject.domain.fin.account.controller;

import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountCreateResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.AccountService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
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
}
