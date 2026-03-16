package com.ssafy.edu.awesomeproject.domain.community.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(
        name = "reports",
        indexes = {
            @Index(name = "idx_reports_target", columnList = "target_type,target_id"),
            @Index(name = "idx_reports_status", columnList = "report_status"),
            @Index(name = "idx_reports_reporter_user_id", columnList = "reporter_user_id")
        })
@Getter
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Report extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "reporter_user_id", nullable = false)
    private Long reporterUserId;

    @Enumerated(EnumType.STRING)
    @Column(name = "target_type", nullable = false, length = 20)
    private ReportTargetType targetType;

    @Column(name = "target_id", nullable = false)
    private Long targetId;

    @Enumerated(EnumType.STRING)
    @Column(name = "reason_code", nullable = false, length = 30)
    private ReportReasonCode reasonCode;

    @Column(name = "detail_text", columnDefinition = "TEXT")
    private String detailText;

    @Enumerated(EnumType.STRING)
    @Column(name = "report_status", nullable = false, length = 20)
    private ReportStatus reportStatus;

    @Column(name = "processed_by_user_id")
    private Long processedByUserId;

    @Column(name = "process_note", columnDefinition = "TEXT")
    private String processNote;

    @Column(name = "processed_at")
    private LocalDateTime processedAt;

    public Report(
            Long reporterUserId,
            ReportTargetType targetType,
            Long targetId,
            ReportReasonCode reasonCode,
            String detailText) {
        this.reporterUserId = reporterUserId;
        this.targetType = targetType;
        this.targetId = targetId;
        this.reasonCode = reasonCode;
        this.detailText = detailText;
        this.reportStatus = ReportStatus.RECEIVED;
    }

    public void blind(Long processedByUserId, String processNote) {
        this.reportStatus = ReportStatus.BLINDED;
        this.processedByUserId = processedByUserId;
        this.processNote = processNote;
        this.processedAt = LocalDateTime.now();
    }

    public void reject(Long processedByUserId, String processNote) {
        this.reportStatus = ReportStatus.REJECTED;
        this.processedByUserId = processedByUserId;
        this.processNote = processNote;
        this.processedAt = LocalDateTime.now();
    }
}
