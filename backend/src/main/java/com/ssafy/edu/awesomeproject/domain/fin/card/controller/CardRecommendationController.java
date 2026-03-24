package com.ssafy.edu.awesomeproject.domain.fin.card.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardRecommendationResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.service.CardService;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("fin/cards")
public class CardRecommendationController {

    private final CardService cardService;

    @GetMapping("/recommend")
    @Operation(summary = "카드 추천 목록 조회", description = "AI를 사용하여 소비 습관 기반 카드를 추천합니다.")
    public ResponseEntity<CardRecommendationResponse> getCardRecommendation(
            @CurrentUserId Long userId,
            @RequestParam String month) {
        CardRecommendationResponse response = cardService.getCardRecommendation(userId, month);
        return ResponseEntity.ok(response);
    }
}
