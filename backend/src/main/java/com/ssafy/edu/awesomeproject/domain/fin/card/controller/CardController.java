package com.ssafy.edu.awesomeproject.domain.fin.card.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.service.CardService;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("fin/cards")
public class CardController {

    private final CardService cardService;

    @GetMapping
    @Operation(summary = "내 카드 목록 조회", description = "현재 로그인 사용자의 카드 목록을 조회합니다.")
    public ResponseEntity<CardListResponse> getMyCards(@CurrentUserId Long userId) {
        CardListResponse response = cardService.getCardList(userId);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/refresh")
    @Operation(summary = "카드 목록 새로고침", description = "외부 API 기준으로 카드 정보를 재동기화합니다.")
    public ResponseEntity<CardListResponse> refreshMyCards(@CurrentUserId Long userId) {
        CardListResponse response = cardService.refreshCardList(userId);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{cardId}")
    @Operation(summary = "카드 결제내역 조회", description = "카드 번호와 기간으로 결제내역을 조회합니다.")
    public ResponseEntity<CardTransactionResponse> getCardTransactions(
        @CurrentUserId Long userId,
        @PathVariable Long cardId,
        @RequestParam String startDate,
        @RequestParam String endDate) {
        CardTransactionResponse response =
            cardService.getCardTransactions(userId, cardId, startDate, endDate);
        return ResponseEntity.ok(response);
    }
}
