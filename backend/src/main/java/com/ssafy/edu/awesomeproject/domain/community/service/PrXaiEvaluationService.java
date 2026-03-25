package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrXaiEvaluationRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiAvailabilityResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiEvaluationResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientResponseException;

@Slf4j
@Service
public class PrXaiEvaluationService {

    private final PrXaiContextService prXaiContextService;
    private final PrXaiAvailabilityService prXaiAvailabilityService;
    private final AiClient aiClient;

    public PrXaiEvaluationService(
            PrXaiContextService prXaiContextService,
            PrXaiAvailabilityService prXaiAvailabilityService,
            AiClient aiClient) {
        this.prXaiContextService = prXaiContextService;
        this.prXaiAvailabilityService = prXaiAvailabilityService;
        this.aiClient = aiClient;
    }

    public PrXaiEvaluationResponseDto evaluate(Long postId, Long userId) {
        PrXaiAvailabilityResponseDto availability =
                prXaiAvailabilityService.checkAvailability(postId, userId);
        if (!availability.enabled()) {
            throw new CommunityException(
                    CommunityErrorCode.PURCHASE_REQUEST_NOT_OPEN,
                    availability.reason());
        }

        PrXaiEvaluationRequestDto request = prXaiContextService.buildContext(postId, userId);
        try {
            PrXaiEvaluationResponseDto response = aiClient.evaluatePrXai(request.requestId(), request);
            if (response == null) {
                throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_XAI_UPSTREAM_ERROR);
            }
            return response;
        } catch (CommunityException exception) {
            throw exception;
        } catch (ResourceAccessException exception) {
            log.warn("PR XAI timeout or connection failure. requestId={}", request.requestId(), exception);
            throw new CommunityException(
                    CommunityErrorCode.PURCHASE_REQUEST_XAI_TIMEOUT,
                    request.requestId());
        } catch (RestClientResponseException exception) {
            log.warn(
                    "PR XAI upstream responded with error. requestId={}, status={}, body={}",
                    request.requestId(),
                    exception.getStatusCode(),
                    exception.getResponseBodyAsString());
            throw new CommunityException(
                    CommunityErrorCode.PURCHASE_REQUEST_XAI_UPSTREAM_ERROR,
                    request.requestId());
        } catch (Exception exception) {
            log.warn("PR XAI unexpected upstream failure. requestId={}", request.requestId(), exception);
            throw new CommunityException(
                    CommunityErrorCode.PURCHASE_REQUEST_XAI_UPSTREAM_ERROR,
                    request.requestId());
        }
    }
}
