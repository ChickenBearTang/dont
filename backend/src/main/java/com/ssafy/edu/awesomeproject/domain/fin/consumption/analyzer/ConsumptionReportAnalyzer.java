package com.ssafy.edu.awesomeproject.domain.fin.consumption.analyzer;

import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardSummaryResponse;
import java.time.LocalDate;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class ConsumptionReportAnalyzer {
    public Map<String, Object> buildBaseMonthlyPayload(
            Long userId, LocalDate reportMonth, CardSummaryResponse cardSummary) {
        List<Map<String, Object>> categorySummary =
                (cardSummary.getRankColumList() == null
                                ? List.<CardSummaryResponse.RankColum>of()
                                : cardSummary.getRankColumList())
                        .stream()
                                .map(
                                        row ->
                                                Map.<String, Object>of(
                                                        "categoryName", row.getCategoryName(),
                                                        "amount", row.getAmount(),
                                                        "percentage", row.getPercentage()))
                                .toList();

        Map<String, Object> topCategory =
                categorySummary.stream()
                        .max(
                                Comparator.comparing(
                                        item ->
                                                ((Number) item.getOrDefault("amount", 0))
                                                        .longValue()))
                        .orElse(Map.of());

        return Map.of(
                "userId", userId,
                "reportMonth", reportMonth.toString(),
                "totalAmount",
                        cardSummary.getTotalAmount() == null ? 0L : cardSummary.getTotalAmount(),
                "topCategory", topCategory,
                "categorySummary", categorySummary);
    }
}
