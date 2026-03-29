package com.ssafy.edu.awesomeproject.domain.fin.consumption.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDate;
import java.util.Map;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Getter
@Entity
@Table(name = "fin_consumption_justification")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class FinConsumptionJustification extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "target_month", nullable = false)
    private LocalDate targetMonth;

    @Column(name = "user_message", nullable = false, columnDefinition = "text")
    private String userMessage;

    @Column(name = "ai_response", nullable = false, columnDefinition = "text")
    private String aiResponse;

    @Column(name = "is_valid", nullable = false)
    private boolean isValid;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "context_payload", columnDefinition = "jsonb")
    private Map<String, Object> contextPayload;

    @Builder
    public FinConsumptionJustification(
            Long userId,
            LocalDate targetMonth,
            String userMessage,
            String aiResponse,
            boolean isValid,
            Map<String, Object> contextPayload) {
        this.userId = userId;
        this.targetMonth = targetMonth;
        this.userMessage = userMessage;
        this.aiResponse = aiResponse;
        this.isValid = isValid;
        this.contextPayload = contextPayload;
    }
}
