package com.ssafy.edu.awesomeproject.domain.fin.secretary.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.AiAnalysisRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.entity.CardTransaction;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request.StrictSecretaryRequest;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response.StrictSecretaryResponse;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class StrictSecretaryService {

    private final UserRepository userRepository;
    private final CardTransactionRepository cardTransactionRepository;
    private final AiClient aiClient;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    public StrictSecretaryResponse evaluatePurchase(Long userId, String itemText, String itemLink, String userReason) {
        User user = userRepository.findById(userId).orElseThrow();
        
        // 최근 2개월간의 카드 결제 내역 수집 (컨텍스트용)
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusMonths(2);
        
        List<CardTransaction> transactions = cardTransactionRepository.findByUserIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(userId, start, end);
        
        List<AiAnalysisRequest.CardTransactionBase> recentTxs = transactions.stream()
            .map(tx -> AiAnalysisRequest.CardTransactionBase.builder()
                .transaction_date(tx.getTransactionDate().format(DATE_FORMATTER))
                .transaction_time(tx.getTransactionTime())
                .merchant_name(tx.getMerchantName())
                .category_name(tx.getCategoryName())
                .transaction_amount(tx.getTransactionAmount())
                .build())
            .collect(Collectors.toList());

        StrictSecretaryRequest request = StrictSecretaryRequest.builder()
            .user_profile(AiAnalysisRequest.UserProfileBase.builder()
                .user_id(String.valueOf(userId))
                .name(user.getName())
                .monthly_income(5000000L) // TODO: 연동
                .build())
            .item_text(itemText)
            .item_link(itemLink)
            .user_reason(userReason)
            .recent_transactions(recentTxs)
            .ai_report_context(null) // TODO: 필요한 경우 최근 리포트 요약 전달
            .build();

        return aiClient.evaluatePurchase(request);
    }
}
