package com.ssafy.edu.awesomeproject.domain.fin.account.controller;

import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingTargetRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.AccountService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/accounts") // URL도 도메인에 맞게 'accounts'로 변경
public class AccountController {

    private final AccountService accountService;

    // 사용자의 수시입출금 계좌 목록을 조회. (주 계좌 설정용)
    @GetMapping
    public ResponseEntity<AccountListResponse> getMyAccounts() {

        Long currentUserId = 1L; // (임시 값)

        AccountListResponse response = accountService.getAccountList(currentUserId);

        return ResponseEntity.ok(response);
    }

    // 특정 계좌의 상세 정보를 조회.
    @GetMapping("/{accountId}")
    public ResponseEntity<AccountResponse> getAccountDetail(@PathVariable Long accountId) {

        Long currentUserId = 1L; // (임시 값)

        AccountResponse response = accountService.getAccount(currentUserId, accountId);

        return ResponseEntity.ok(response);
    }

    // 신규 '세이브 박스' 계좌 개설.
    @PostMapping("/save-box")
    public ResponseEntity<AccountResponse> createSaveBox(
            @RequestBody SaveBoxCreateRequest request) {

        Long currentUserId = 1L; // (임시 값)

        AccountResponse response = accountService.createSaveBox(currentUserId, request);

        return ResponseEntity.ok(response);
    }

    // 저축 목표 금액 설정/변경.
    @PatchMapping("/{accountId}/saving-target")
    public ResponseEntity<AccountResponse> updateSavingTargetAmount(
            @PathVariable Long accountId, @RequestBody SavingTargetRequest request) {

        Long currentUserId = 1L; // (임시 값)

        AccountResponse response =
                accountService.updateSavingTargetAmount(currentUserId, accountId, request);

        return ResponseEntity.ok(response);
    }

    // 특정 계좌를 '주 계좌'로 설정.
    @PatchMapping("/{accountId}/primary")
    public ResponseEntity<AccountResponse> setPrimaryAccount(@PathVariable Long accountId) {

        Long currentUserId = 1L; // (임시 값)

        AccountResponse response = accountService.setPrimaryAccount(currentUserId, accountId);

        return ResponseEntity.ok(response);
    }
}
