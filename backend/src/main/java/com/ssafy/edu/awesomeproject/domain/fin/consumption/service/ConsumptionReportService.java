package com.ssafy.edu.awesomeproject.domain.fin.consumption.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardRecommendationResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.service.CardService;
import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.client.ConsumptionAiClient;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request.GenerateMonthlyReportRequest;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.AvgCohort;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.JustificationEvaluationResponse;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response.MonthlyReportResponse;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.FinConsumptionJustification;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.FinConsumptionMonthlyReport;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.MonthlyReportGenerationSource;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.MonthlyReportLlmStatus;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.MonthlyReportStatus;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.error.ConsumptionErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.error.ConsumptionException;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.repository.FinConsumptionJustificationRepository;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.repository.FinConsumptionMonthlyReportRepository;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import java.math.BigDecimal;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeParseException;
import java.util.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Slf4j
@RequiredArgsConstructor
@Transactional
public class ConsumptionReportService {

    private final FinConsumptionMonthlyReportRepository monthlyReportRepository;
    private final FinConsumptionJustificationRepository justificationRepository;
    private final UserRepository userRepository;
    private final CardTransactionRepository cardTransactionRepository;
    private final CardService cardService;

    private final ConsumptionAiClient consumptionAiClient;
    private final ObjectMapper objectMapper;
    private final Clock applicationClock;
    private final NotificationService notificationService;


    public MonthlyReportResponse generateMonthlyReport(
        Long userId,
        GenerateMonthlyReportRequest request,
        MonthlyReportGenerationSource source) {
        LocalDate reportMonth = toMonthStart(request.reportMonth());
        return generateMonthlyReport(userId, reportMonth, source);
    }

    private MonthlyReportResponse generateMonthlyReport(
        Long userId, LocalDate reportMonth, MonthlyReportGenerationSource source) {
        FinConsumptionMonthlyReport latest =
            monthlyReportRepository
                .findTopByUserIdAndReportMonthAndIsLatestTrue(userId, reportMonth)
                .orElse(null);

        String transactionFingerprint = buildTransactionFingerprint(userId, reportMonth);
        CardRecommendationResponse previousCardRecommendation =
            latest == null ? null : extractCardRecommendation(latest.getReportPayload());
        String previousFingerprint =
            latest == null ? null : extractTransactionFingerprint(latest.getReportPayload());

        if (latest != null) {
            latest.markNotLatest();
        }

        int nextVersion =
            monthlyReportRepository
                .findTopByUserIdAndReportMonthOrderByVersionNoDesc(userId, reportMonth)
                .map(existing -> existing.getVersionNo() + 1)
                .orElse(1);

        ConsumptionAiClient.AiReportAnalysis aiAnalysis =
            consumptionAiClient.analyzeMonthlyReport(userId, reportMonth.toString());

        boolean recommendationReused =
            previousCardRecommendation != null
                && Objects.equals(previousFingerprint, transactionFingerprint);
        CardRecommendationResponse cardRecommendation =
            recommendationReused
                ? previousCardRecommendation
                : loadCardRecommendation(userId, reportMonth.toString());

        List<Map<String, Object>> validJustifications =
            loadValidJustificationsForReport(userId, reportMonth);

        Map<String, Object> reportPayload = new LinkedHashMap<>();
        reportPayload.put("justifications", validJustifications);
        reportPayload.put("cardRecommendation", toMap(cardRecommendation));
        reportPayload.put("aiAnalysis", aiAnalysis.analysisPayload());
        reportPayload.put(
            "meta",
            buildReportMeta(
                aiAnalysis.llmStatus(),
                cardRecommendation,
                recommendationReused,
                transactionFingerprint));

        FinConsumptionMonthlyReport report =
            FinConsumptionMonthlyReport.builder()
                .userId(userId)
                .reportMonth(reportMonth)
                .llmStatus(toLlmStatus(aiAnalysis.llmStatus()))
                .reportStatus(MonthlyReportStatus.FINAL)
                .generationSource(source)
                .reportPayload(reportPayload)
                .versionNo(nextVersion)
                .isLatest(true)
                .generatedAt(LocalDateTime.now(applicationClock))
                .build();

        FinConsumptionMonthlyReport saved = monthlyReportRepository.save(report);

        if (source == MonthlyReportGenerationSource.MANUAL) {
            createConsumptionReportReadyNotification(userId, reportMonth);
        }

        return toResponse(saved);
    }

    public MonthlyReportResponse getLatestMonthlyReport(Long userId, String reportMonthText) {
        LocalDate reportMonth = toMonthStart(reportMonthText);
        FinConsumptionMonthlyReport report =
            monthlyReportRepository
                .findTopByUserIdAndReportMonthAndIsLatestTrue(userId, reportMonth)
                .orElseThrow(
                    () ->
                        new ConsumptionException(
                            ConsumptionErrorCode.REPORT_NOT_FOUND));

        String yearMonth = YearMonth.from(reportMonth).toString();
        Map<String, Object> enrichedPayload =
            ensureCardRecommendationInPayload(report.getReportPayload(), userId, yearMonth);

        if (!Objects.equals(report.getReportPayload(), enrichedPayload)) {
            report.replaceReportPayload(enrichedPayload);
            monthlyReportRepository.save(report);
        }
        return toResponse(report, enrichedPayload);
    }

    public JustificationEvaluationResponse evaluateAndSaveJustification(
        Long userId, String targetMonthText, String message) {
        LocalDate targetMonth = toMonthStart(targetMonthText);
        String targetYearMonth = YearMonth.from(targetMonth).toString();

        ConsumptionAiClient.JustificationEvaluation evaluation =
            consumptionAiClient.evaluateJustification(userId, targetYearMonth, message);

        Map<String, Object> context =
            monthlyReportRepository
                .findTopByUserIdAndReportMonthAndIsLatestTrue(userId, targetMonth)
                .map(FinConsumptionMonthlyReport::getReportPayload)
                .orElse(Map.of());

        FinConsumptionJustification saved =
            justificationRepository.save(
                FinConsumptionJustification.builder()
                    .userId(userId)
                    .targetMonth(targetMonth)
                    .userMessage(message)
                    .aiResponse(evaluation.response())
                    .isValid(evaluation.valid())
                    .contextPayload(context)
                    .build());

        MonthlyReportResponse regeneratedReport = null;
        boolean reportRegenerated = false;
        if (evaluation.valid()) {
            regeneratedReport =
                generateMonthlyReport(userId, targetMonth, MonthlyReportGenerationSource.RETRY);
            reportRegenerated = true;
        }

        return new JustificationEvaluationResponse(
            saved.getId(),
            saved.getTargetMonth().toString(),
            saved.isValid(),
            saved.getUserMessage(),
            saved.getAiResponse(),
            saved.getCreatedAt(),
            reportRegenerated,
            regeneratedReport);
    }

    private void createConsumptionReportReadyNotification(Long userId, LocalDate reportMonth) {
        User user =
            userRepository
                .findById(userId)
                .orElseThrow(
                    () ->
                        new ConsumptionException(
                            ConsumptionErrorCode.REPORT_NOT_FOUND));

        String displayName =
            user.getNickname() != null && !user.getNickname().isBlank()
                ? user.getNickname()
                : user.getName();

        int year = reportMonth.getYear();
        int month = reportMonth.getMonthValue();
        long referenceMonth = Long.parseLong(String.format("%04d%02d", year, month));

        notificationService.createNotification(
            userId,
            NotificationType.CONSUMPTION_REPORT_READY,
            "소비 리포트 도착",
            String.format(
                "%s님의 %d년 %d월 소비 리포트가 도착했어요! 확인해보세요!",
                displayName, year, month),
            NotificationReferenceType.FINANCE,
            referenceMonth);
    }

    private MonthlyReportResponse toResponse(FinConsumptionMonthlyReport saved) {
        return toResponse(saved, saved.getReportPayload());
    }

    private MonthlyReportResponse toResponse(
        FinConsumptionMonthlyReport saved, Map<String, Object> reportPayload) {
        return new MonthlyReportResponse(
            saved.getId(),
            saved.getReportMonth().toString(),
            saved.getVersionNo(),
            saved.isLatest(),
            saved.getLlmStatus(),
            saved.getReportStatus(),
            saved.getGenerationSource(),
            saved.getGeneratedAt(),
            reportPayload);
    }

    private LocalDate toMonthStart(String reportMonthText) {
        try {
            return YearMonth.parse(reportMonthText).atDay(1);
        } catch (DateTimeParseException exception) {
            throw new ConsumptionException(
                ConsumptionErrorCode.INVALID_REPORT_MONTH, reportMonthText);
        }
    }

    private MonthlyReportLlmStatus toLlmStatus(String llmStatus) {
        return switch (llmStatus.toLowerCase()) {
            case "ok" -> MonthlyReportLlmStatus.OK;
            case "degraded" -> MonthlyReportLlmStatus.DEGRADED;
            default -> MonthlyReportLlmStatus.SKIPPED;
        };
    }

    private List<Map<String, Object>> loadValidJustificationsForReport(
        Long userId, LocalDate targetMonth) {
        return justificationRepository
            .findAllByUserIdAndTargetMonthOrderByCreatedAtDesc(userId, targetMonth)
            .stream()
            .filter(FinConsumptionJustification::isValid)
            .sorted(Comparator.comparing(FinConsumptionJustification::getCreatedAt))
            .map(
                row -> {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("id", row.getId());
                    item.put("message", row.getUserMessage());
                    item.put("aiResponse", row.getAiResponse());
                    item.put("createdAt", row.getCreatedAt());
                    return item;
                })
            .toList();
    }

    private CardRecommendationResponse loadCardRecommendation(Long userId, String reportMonth) {
        try {
            CardRecommendationResponse response = cardService.getCardRecommendation(userId, reportMonth);
            if (response == null) {
                log.warn(
                    "Card recommendation returned null. userId={}, reportMonth={}",
                    userId,
                    reportMonth);
            }
            return response;
        } catch (Exception exception) {
            log.warn(
                "Card recommendation load failed. userId={}, reportMonth={}",
                userId,
                reportMonth,
                exception);
            return null;
        }
    }

    private Map<String, Object> ensureCardRecommendationInPayload(
        Map<String, Object> payload, Long userId, String reportMonth) {
        Map<String, Object> mergedPayload = payload == null ? new LinkedHashMap<>() : new LinkedHashMap<>(payload);
        String transactionFingerprint = buildTransactionFingerprint(userId, toMonthStart(reportMonth));
        Object existingCardRecommendation = mergedPayload.get("cardRecommendation");
        if (hasCardRecommendation(existingCardRecommendation)) {
            mergedPayload.put(
                "meta",
                mergeReportMeta(mergedPayload, "OK", null, transactionFingerprint));
            return mergedPayload;
        }

        CardRecommendationResponse cardRecommendation = loadCardRecommendation(userId, reportMonth);
        mergedPayload.put("cardRecommendation", toMap(cardRecommendation));
        String recommendationStatus = cardRecommendation == null ? "FAILED" : "OK";
        mergedPayload.put(
            "meta",
            mergeReportMeta(mergedPayload, recommendationStatus, false, transactionFingerprint));
        return mergedPayload;
    }

    private boolean hasCardRecommendation(Object value) {
        if (value instanceof Map<?, ?> map) {
            return !map.isEmpty();
        }
        return value != null;
    }

    private Map<String, Object> toMap(CardRecommendationResponse cardRecommendation) {
        if (cardRecommendation == null) {
            return Map.of();
        }
        return objectMapper.convertValue(cardRecommendation, Map.class);
    }

    private String buildTransactionFingerprint(Long userId, LocalDate reportMonth) {
        LocalDate startDate = reportMonth.withDayOfMonth(1);
        LocalDate endDate = reportMonth.withDayOfMonth(reportMonth.lengthOfMonth());
        CardTransactionRepository.MonthlyTransactionSnapshotProjection snapshot =
            cardTransactionRepository.findMonthlyTransactionSnapshot(userId, startDate, endDate);
        if (snapshot == null) {
            return "0:0:-:-";
        }
        long txCount = snapshot.getTxCount() == null ? 0L : snapshot.getTxCount();
        long totalAmount = snapshot.getTotalAmount() == null ? 0L : snapshot.getTotalAmount();
        String lastDate = snapshot.getLastDate() == null ? "-" : snapshot.getLastDate().toString();
        String lastTime = snapshot.getLastTime() == null ? "-" : snapshot.getLastTime();
        return txCount + ":" + totalAmount + ":" + lastDate + ":" + lastTime;
    }

    private CardRecommendationResponse extractCardRecommendation(Map<String, Object> reportPayload) {
        if (reportPayload == null) {
            return null;
        }
        Object recommendation = reportPayload.get("cardRecommendation");
        if (!(recommendation instanceof Map<?, ?> recommendationMap) || recommendationMap.isEmpty()) {
            return null;
        }
        try {
            return objectMapper.convertValue(recommendationMap, CardRecommendationResponse.class);
        } catch (IllegalArgumentException exception) {
            log.warn("Failed to parse stored cardRecommendation payload", exception);
            return null;
        }
    }

    private String extractTransactionFingerprint(Map<String, Object> reportPayload) {
        if (reportPayload == null) {
            return null;
        }
        Object meta = reportPayload.get("meta");
        if (!(meta instanceof Map<?, ?> metaMap)) {
            return null;
        }
        Object fingerprint = metaMap.get("transactionFingerprint");
        return fingerprint == null ? null : String.valueOf(fingerprint);
    }

    private Map<String, Object> buildReportMeta(
        String llmStatus,
        CardRecommendationResponse cardRecommendation,
        boolean recommendationReused,
        String transactionFingerprint) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("analysisStatus", normalizeAnalysisStatus(llmStatus));
        meta.put("recommendationStatus", cardRecommendation == null ? "FAILED" : "OK");
        meta.put("recommendationReused", recommendationReused);
        meta.put("transactionFingerprint", transactionFingerprint);
        return meta;
    }

    private Map<String, Object> mergeReportMeta(
        Map<String, Object> reportPayload,
        String recommendationStatus,
        Boolean recommendationReused,
        String transactionFingerprint) {
        Map<String, Object> meta = new LinkedHashMap<>();
        Object currentMeta = reportPayload.get("meta");
        if (currentMeta instanceof Map<?, ?> currentMetaMap) {
            for (Map.Entry<?, ?> entry : currentMetaMap.entrySet()) {
                if (entry.getKey() != null) {
                    meta.put(String.valueOf(entry.getKey()), entry.getValue());
                }
            }
        }

        meta.put("recommendationStatus", recommendationStatus);
        if (recommendationReused != null) {
            meta.put("recommendationReused", recommendationReused);
        }
        if (transactionFingerprint != null) {
            meta.put("transactionFingerprint", transactionFingerprint);
        }
        return meta;
    }

    private String normalizeAnalysisStatus(String llmStatus) {
        if (llmStatus == null || llmStatus.isBlank()) {
            return "SKIPPED";
        }
        return llmStatus.trim().toUpperCase(Locale.ROOT);
    }
    @Transactional(readOnly = true)
    public AvgCohort avgCohort(Long userId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () ->
                                        new ConsumptionException(
                                                ConsumptionErrorCode.INVALID_PAYLOAD,
                                                "User not found: " + userId));

        if (user.getCohort() == null) {
            throw new ConsumptionException(
                    ConsumptionErrorCode.INVALID_PAYLOAD,
                    "Cohort is missing for userId=" + userId);
        }

        Long cohortId = user.getCohort().getId();
        LocalDate endDate = LocalDate.now(applicationClock);
        LocalDate startDate = endDate.withDayOfMonth(1);

        CardTransactionRepository.CohortCategoryAverageProjection projection =
                cardTransactionRepository.findCohortCategoryAverages(
                        cohortId, userId, startDate, endDate);

        if (projection == null) {
            return new AvgCohort(cohortId, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        }

        return new AvgCohort(
                projection.getCohortId(),
                0.0,
                toDouble(projection.getAvgFood()),
                toDouble(projection.getAvgCafe()),
                toDouble(projection.getAvgCulture()),
                toDouble(projection.getAvgMarket()),
                toDouble(projection.getAvgMedical()));
    }

    private double toDouble(BigDecimal value) {
        return value == null ? 0.0 : value.doubleValue();
    }
}
