package com.ssafy.edu.awesomeproject.domain.fin.card.controller;

import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.service.CardService;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/cards")

public class CardController {

    private final CardService cardService;

    //카드 목록 불러오기
    @GetMapping
    @Operation(summary = "내 카드 목록 조회", description = "현재 로그인 사용자의 카드 목록을 조회합니다.")
    public ResponseEntity<CardListResponse> getMyCards() {
        Long currentUserId = 1L; // TODO: Replace with authenticated user ID
        CardListResponse response = cardService.getCardList(currentUserId);
        return ResponseEntity.ok(response);
    }

    //카드 결제내역 불러오기
    @GetMapping("/{cardNo}")
    @Operation(summary = "한 카드의 결제내역 조회", description = "카드 정보와 날짜를 입력하면 기간의 결제내역이 뜹니다.")
    public ResponseEntity<CardTransactionResponse> getCardTransactions(
        @PathVariable String cardNo,
        @RequestParam String startDate,
        @RequestParam String endDate) {
        Long currentUserId = 1L; // TODO: Replace with authenticated user ID
        CardTransactionResponse response =
            cardService.getCardTransactions(currentUserId, cardNo, startDate, endDate);
        return ResponseEntity.ok(response);
    }
}
