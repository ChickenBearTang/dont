package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.OffsetDateTime;
import java.util.List;

public record PrXaiEvaluationResponseDto(
        String requestId,
        Long purchaseRequestId,
        String decision,
        String summary,
        PrXaiSectionDto financialEvaluation,
        PrXaiSectionDto priceEvaluation,
        List<PrXaiTopFactorDto> topFactors,
        List<PrXaiEvidenceDto> supportingEvidence,
        List<PrXaiCounterfactualDto> counterfactuals,
        List<String> warnings,
        PrXaiConfidenceDto confidence,
        PrXaiRuntimeEnginesDto runtimeEngines,
        OffsetDateTime generatedAt,
        String schemaVersion,
        String modelVersion,
        String ruleVersion) {}
