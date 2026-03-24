package com.ssafy.edu.awesomeproject.domain.fin.consumption.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.card.dto.response.CardSummaryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.service.CardService;
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
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Comparator;
import java.util.LinkedHashMap;
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
    private final UserRepository userRepository;
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
        List<Map<String, Object>> validJustifications =
            loadValidJustificationsForReport(userId, reportMonth);
        Map<String, Object> aiInputPayload =
            Map.of("base", basePayload, "justifications", validJustifications);
        ConsumptionAiClient.AiReportAnalysis aiAnalysis =
            consumptionAiClient.analyzeMonthlyReport(aiInputPayload);

        Map<String, Object> reportPayload =
            Map.of(
                "base",
                basePayload,
                "justifications",
                validJustifications,
                "aiAnalysis",
                aiAnalysis.analysisPayload());

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

    @Transactional(readOnly = true)
    public MonthlyReportResponse getLatestMonthlyReport(Long userId, String reportMonthText) {
        LocalDate reportMonth = toMonthStart(reportMonthText);
        FinConsumptionMonthlyReport report =
            monthlyReportRepository
                .findTopByUserIdAndReportMonthAndIsLatestTrue(userId, reportMonth)
                .orElseThrow(
                    () ->
                        new ConsumptionException(
                            ConsumptionErrorCode.REPORT_NOT_FOUND));
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
        List<Map<String, String>> history =
            toHistory(
                justificationRepository.findAllByUserIdAndTargetMonthOrderByCreatedAtDesc(
                    userId, targetMonth));

        ConsumptionAiClient.JustificationEvaluation evaluation =
            consumptionAiClient.evaluateJustification(message, context, history);

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
            "소비리포트 도착",
            String.format(
                "%s님의 %d년 %d월 소비리포트가 도착했어요! 확인해보세요!",
                displayName, year, month),
            NotificationReferenceType.FINANCE,
            referenceMonth);
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

    private List<Map<String, String>> toHistory(List<FinConsumptionJustification> rows) {
        return rows.stream()
            .sorted(Comparator.comparing(FinConsumptionJustification::getCreatedAt))
            .flatMap(
                row ->
                    List.of(
                            Map.of("role", "user", "message", row.getUserMessage()),
                            Map.of("role", "assistant", "message", row.getAiResponse()))
                        .stream())
            .toList();
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
}
