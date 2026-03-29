package com.ssafy.edu.awesomeproject.domain.fin.profile.controller;

import com.ssafy.edu.awesomeproject.domain.fin.profile.dto.response.FinanceProfileResponse;
import com.ssafy.edu.awesomeproject.domain.fin.profile.service.FinanceProfileService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Finance Profile", description = "XAI 연동용 재무 프로필 API")
@RestController
@RequestMapping("/users")
public class FinanceProfileController {

    private final FinanceProfileService financeProfileService;

    public FinanceProfileController(FinanceProfileService financeProfileService) {
        this.financeProfileService = financeProfileService;
    }

    @Operation(summary = "재무 프로필 조회", description = "XAI 분석용 재무 프로필을 반환합니다.")
    @GetMapping("/{userId}/finance-profile")
    public ResponseEntity<FinanceProfileResponse> getFinanceProfile(@PathVariable String userId) {
        return ResponseEntity.ok(financeProfileService.getFinanceProfile(userId));
    }
}
