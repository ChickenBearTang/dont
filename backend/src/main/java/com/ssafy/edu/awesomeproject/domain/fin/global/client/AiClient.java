package com.ssafy.edu.awesomeproject.domain.fin.global.client;

import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.AiAnalysisRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.AiAnalysisResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.CardRecommendationRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardRecommendationResponse;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request.StrictSecretaryRequest;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response.StrictSecretaryResponse;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.service.annotation.PostExchange;

public interface AiClient {
    @PostExchange("/api/v1/analyze")
    AiAnalysisResponse analyzeConsumption(@RequestBody AiAnalysisRequest request);

    @PostExchange("/api/v1/strict-sec")
    StrictSecretaryResponse evaluatePurchase(@RequestBody StrictSecretaryRequest request);

    @PostExchange("/api/v1/strict-sec/tts")
    byte[] getTtsAudio(
            @RequestBody
                    com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request.TtsRequest
                            request);
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.CardRecommendationRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardRecommendationResponse;

    @PostExchange("/api/v1/recommendation/calculate")
    CardRecommendationResponse getCardRecommendation(@RequestBody CardRecommendationRequest request);
}
