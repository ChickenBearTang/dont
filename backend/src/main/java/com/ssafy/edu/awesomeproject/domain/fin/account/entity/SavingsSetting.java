package com.ssafy.edu.awesomeproject.domain.fin.account.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "savings_settings")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class SavingsSetting {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "primary_account_id", nullable = false)
    private Long primaryAccountId;

    @Column(name = "savebox_account_id", nullable = false)
    private Long saveboxAccountId;

    @Column(name = "keyword", nullable = false, length = 100)
    private String keyword;

    @Column(name = "savings_amount", nullable = false, precision = 15, scale = 2)
    private BigDecimal savingsAmount;

    @Column(name = "is_active", nullable = false)
    private boolean isActive;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Builder
    public SavingsSetting(
            Long userId,
            Long primaryAccountId,
            Long saveboxAccountId,
            String keyword,
            BigDecimal savingsAmount,
            boolean isActive) {
        this.userId = userId;
        this.primaryAccountId = primaryAccountId;
        this.saveboxAccountId = saveboxAccountId;
        this.keyword = keyword;
        this.savingsAmount = savingsAmount;
        this.isActive = isActive;
    }

    public void update(String keyword, BigDecimal savingsAmount, boolean isActive) {
        this.keyword = keyword;
        this.savingsAmount = savingsAmount;
        this.isActive = isActive;
    }

    public void activate() {
        this.isActive = true;
    }

    public void deactivate() {
        this.isActive = false;
    }

    public void updatePrimaryAccount(Long primaryAccountId) {
        this.primaryAccountId = primaryAccountId;
    }
}
