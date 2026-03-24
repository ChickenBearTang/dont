package com.ssafy.edu.awesomeproject.domain.fin.secretary.service;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request.StrictSecretaryDbRequest;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response.StrictSecretaryResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class StrictSecretaryService {

    private final AiClient aiClient;

    public StrictSecretaryResponse evaluatePurchase(
            Long userId, String itemText, String itemLink, String userReason) {
        return aiClient.evaluatePurchaseFromDb(
                new StrictSecretaryDbRequest(userId, itemText, itemLink, userReason));
    }
}
