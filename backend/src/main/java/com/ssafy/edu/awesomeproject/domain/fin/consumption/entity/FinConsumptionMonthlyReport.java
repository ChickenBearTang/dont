package com.ssafy.edu.awesomeproject.domain.fin.consumption.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Getter
@Entity
@Table(name = "fin_consumption_monthly_report")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class FinConsumptionMonthlyReport extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "report_month", nullable = false)
    private LocalDate reportMonth;

    @Enumerated(EnumType.STRING)
    @Column(name = "llm_status", nullable = false, length = 16)
    private MonthlyReportLlmStatus llmStatus;

    @Enumerated(EnumType.STRING)
    @Column(name = "report_status", nullable = false, length = 16)
    private MonthlyReportStatus reportStatus;

    @Enumerated(EnumType.STRING)
    @Column(name = "generation_source", nullable = false, length = 16)
    private MonthlyReportGenerationSource generationSource;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "report_payload", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> reportPayload;

    @Column(name = "version_no", nullable = false)
    private Integer versionNo;

    @Column(name = "is_latest", nullable = false)
    private boolean isLatest;

    @Column(name = "generated_at", nullable = false)
    private LocalDateTime generatedAt;

    @Builder
    public FinConsumptionMonthlyReport(
            Long userId,
            LocalDate reportMonth,
            MonthlyReportLlmStatus llmStatus,
            MonthlyReportStatus reportStatus,
            MonthlyReportGenerationSource generationSource,
            Map<String, Object> reportPayload,
            Integer versionNo,
            boolean isLatest,
            LocalDateTime generatedAt) {
        this.userId = userId;
        this.reportMonth = reportMonth;
        this.llmStatus = llmStatus;
        this.reportStatus = reportStatus;
        this.generationSource = generationSource;
        this.reportPayload = reportPayload;
        this.versionNo = versionNo;
        this.isLatest = isLatest;
        this.generatedAt = generatedAt;
    }

    public void markNotLatest() {
        this.isLatest = false;
    }

    public void replaceReportPayload(Map<String, Object> reportPayload) {
        this.reportPayload = reportPayload;
    }
}
