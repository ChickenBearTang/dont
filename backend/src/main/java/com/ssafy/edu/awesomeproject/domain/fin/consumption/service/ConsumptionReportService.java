package com.ssafy.edu.awesomeproject.domain.fin.consumption.service;

import com.ssafy.edu.awesomeproject.domain.fin.consumption.analyzer.ConsumptionReportAnalyzer;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.client.ConsumptionAiClient;
import com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.request.GenerateMonthlyReportRequest;
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
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardSummaryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.service.CardService;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class ConsumptionReportService {

    private final FinConsumptionMonthlyReportRepository monthlyReportRepository;
    private final FinConsumptionJustificationRepository justificationRepository;
    private final ConsumptionReportAnalyzer consumptionReportAnalyzer;
    private final ConsumptionAiClient consumptionAiClient;
    private final CardService cardService;
    private final Clock applicationClock;

    public MonthlyReportResponse generateMonthlyReport(
            Long userId,
            GenerateMonthlyReportRequest request,
            MonthlyReportGenerationSource source) {
        LocalDate reportMonth = toMonthStart(request.reportMonth());
        FinConsumptionMonthlyReport latest =
                monthlyReportRepository
                        .findTopByUserIdAndReportMonthAndIsLatestTrue(userId, reportMonth)
                        .orElse(null);

        if (latest != null) {
            latest.markNotLatest();
        }

        int nextVersion =
                monthlyReportRepository
                        .findTopByUserIdAndReportMonthOrderByVersionNoDesc(userId, reportMonth)
                        .map(existing -> existing.getVersionNo() + 1)
                        .orElse(1);

        CardSummaryResponse cardSummary = resolveCardSummary(userId, reportMonth);
        Map<String, Object> basePayload =
                consumptionReportAnalyzer.buildBaseMonthlyPayload(userId, reportMonth, cardSummary);
        ConsumptionAiClient.AiReportAnalysis aiAnalysis =
                consumptionAiClient.analyzeMonthlyReport(basePayload);

        Map<String, Object> reportPayload =
                Map.of(
                        "base", basePayload,
                        "aiAnalysis", aiAnalysis.analysisPayload());

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
        return toResponse(saved);
    }

    @Transactional(readOnly = true)
    public MonthlyReportResponse getLatestMonthlyReport(Long userId, String reportMonthText) {
        LocalDate reportMonth = toMonthStart(reportMonthText);
        FinConsumptionMonthlyReport report =
                monthlyReportRepository
                        .findTopByUserIdAndReportMonthAndIsLatestTrue(userId, reportMonth)
                        .orElseThrow(() -> new ConsumptionException(ConsumptionErrorCode.REPORT_NOT_FOUND));
        return toResponse(report);
    }

    public JustificationEvaluationResponse evaluateAndSaveJustification(
            Long userId, String targetMonthText, String message) {
        LocalDate targetMonth = toMonthStart(targetMonthText);
        Map<String, Object> context =
                monthlyReportRepository
                        .findTopByUserIdAndReportMonthAndIsLatestTrue(userId, targetMonth)
                        .map(FinConsumptionMonthlyReport::getReportPayload)
                        .orElse(Map.of());

        ConsumptionAiClient.JustificationEvaluation evaluation =
                consumptionAiClient.evaluateJustification(message, context, List.of());

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

        return new JustificationEvaluationResponse(
                saved.getId(),
                saved.getTargetMonth().toString(),
                saved.isValid(),
                saved.getUserMessage(),
                saved.getAiResponse(),
                saved.getCreatedAt());
    }

    private MonthlyReportResponse toResponse(FinConsumptionMonthlyReport saved) {
        return new MonthlyReportResponse(
                saved.getId(),
                saved.getReportMonth().toString(),
                saved.getVersionNo(),
                saved.isLatest(),
                saved.getLlmStatus(),
                saved.getReportStatus(),
                saved.getGenerationSource(),
                saved.getGeneratedAt(),
                saved.getReportPayload());
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

    private CardSummaryResponse resolveCardSummary(Long userId, LocalDate reportMonth) {
        LocalDate monthStart = reportMonth.withDayOfMonth(1);
        LocalDate monthEnd = reportMonth.withDayOfMonth(reportMonth.lengthOfMonth());
        String startDate = monthStart.format(DateTimeFormatter.BASIC_ISO_DATE);
        String endDate = monthEnd.format(DateTimeFormatter.BASIC_ISO_DATE);
        return cardService.getCardSummary(userId, startDate, endDate);
    }
}
