package com.ssafy.edu.awesomeproject.domain.fin.account.controller;

import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.FinService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/fin")
public class FinController {

    private final FinService finService;

    // 사용자의 수시입출금 계좌 목록을 조회. (주 계좌 설정용)
    @GetMapping("/accounts")
    public ResponseEntity<AccountListResponse> getMyAccounts() {

        Long currentUserId = 1L; // (임시 값)

        AccountListResponse response = finService.getAccountList(currentUserId);

        return ResponseEntity.ok(response);
    }
}
