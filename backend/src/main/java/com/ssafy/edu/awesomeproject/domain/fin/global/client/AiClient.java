package com.ssafy.edu.awesomeproject.domain.fin.global.client;

import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.AiCardRecommendationDbRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.AiDateRangeRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.AiAnalysisResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardRecommendationResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiEvaluationRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request.AiMonthlyReportRequest;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.AiMonthlyReportAnalysisResponse;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.service.annotation.PostExchange;

public interface AiClient {
    @PostExchange("/api/v1/consumption/date-range-report")
    AiAnalysisResponse analyzeConsumptionByDateRange(@RequestBody AiDateRangeRequest request);

    @PostExchange("/api/v1/xai/purchase-evaluations")
    PrXaiEvaluationResponseDto evaluatePrXai(
            @RequestHeader("X-Request-Id") String requestId,
            @RequestBody PrXaiEvaluationRequestDto request);

    @PostExchange("/api/v1/recommendation/db")
    CardRecommendationResponse getCardRecommendationFromDb(
            @RequestBody AiCardRecommendationDbRequest request);

    @PostExchange("/api/v1/consumption/monthly-report")
    AiMonthlyReportAnalysisResponse analyzeMonthlyReport(@RequestBody AiMonthlyReportRequest request);
}
