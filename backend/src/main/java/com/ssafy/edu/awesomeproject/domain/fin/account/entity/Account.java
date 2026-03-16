package com.ssafy.edu.awesomeproject.domain.fin.account.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "accounts") // 1. 실제 DB 테이블 이름이 'accounts'임을 명시
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class Account {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "account_no", unique = true, nullable = false, length = 30)
    private String accountNo;

    @Column(name = "bank_code", nullable = false, length = 10)
    private String bankCode;

    @Column(name = "bank_name", nullable = false, length = 100)
    private String bankName;

    @Column(name = "account_role", nullable = false, length = 20)
    private String accountRole;

    @Column(name = "is_primary", nullable = false)
    private boolean isPrimary; // 2. isMainAccount -> isPrimary로 DB와 일치

    @Column(name = "account_type_unique_no", length = 50)
    private String accountTypeUniqueNo;

    @Column(name = "account_type_code", length = 20)
    private String accountTypeCode;

    @Column(name = "account_type_name", length = 100)
    private String accountTypeName;

    @Column(name = "account_name", length = 100)
    private String accountName;

    @Column(name = "account_created_date")
    private LocalDate accountCreatedDate;

    @Column(name = "account_expiry_date")
    private LocalDate accountExpiryDate;

    @Column(name = "daily_transfer_limit", precision = 15, scale = 2)
    private BigDecimal dailyTransferLimit;

    @Column(name = "one_time_transfer_limit", precision = 15, scale = 2)
    private BigDecimal oneTimeTransferLimit;

    @Column(name = "balance", nullable = false, precision = 15, scale = 2)
    private BigDecimal balance; // 3. 금액/잔액은 Long 대신 BigDecimal 사용

    @Column(name = "last_transaction_date")
    private LocalDate lastTransactionDate;

    @Column(name = "currency_code", length = 10)
    private String currencyCode; // 4. currency -> currencyCode로 DB와 일치

    @Column(name = "is_verified", nullable = false)
    private boolean isVerified;

    @Column(name = "verified_at")
    private LocalDateTime verifiedAt;

    @Column(name = "status", nullable = false, length = 20)
    private String status;

    @CreationTimestamp // 5. 엔티티 생성 시 자동으로 현재 시간 저장
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp // 5. 엔티티 수정 시 자동으로 현재 시간 저장
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    // --- 6. API 분석을 통해 추가한 컬럼들 ---
    @Column(name = "account_description", length = 500)
    private String accountDescription;

    @Column(name = "account_type", length = 20)
    private String accountType;

    @Column(name = "currency_name", length = 20)
    private String currencyName;

    @Column(name = "user_name", length = 100)
    private String userName;

    @Column(name = "saving_target_amount")
    private Long savingTargetAmount;

    @Builder
    public Account(
            Long userId,
            String accountNo,
            String bankCode,
            String bankName,
            String accountRole,
            String accountTypeUniqueNo,
            String accountTypeCode,
            String accountTypeName,
            String accountName,
            LocalDate accountCreatedDate,
            LocalDate accountExpiryDate,
            boolean isPrimary,
            BigDecimal dailyTransferLimit,
            BigDecimal oneTimeTransferLimit,
            BigDecimal balance,
            LocalDate lastTransactionDate,
            String currencyCode,
            String status,
            String accountDescription,
            String accountType,
            String currencyName,
            String userName) {
        this.userId = userId;
        this.accountNo = accountNo;
        this.bankCode = bankCode;
        this.bankName = bankName;
        this.accountRole = accountRole;
        this.isPrimary = isPrimary;
        this.accountTypeUniqueNo = accountTypeUniqueNo;
        this.accountTypeCode = accountTypeCode;
        this.accountTypeName = accountTypeName;
        this.accountName = accountName;
        this.accountCreatedDate = accountCreatedDate;
        this.accountExpiryDate = accountExpiryDate;
        this.dailyTransferLimit = dailyTransferLimit;
        this.oneTimeTransferLimit = oneTimeTransferLimit;
        this.balance = balance;
        this.lastTransactionDate = lastTransactionDate;
        this.currencyCode = currencyCode;
        this.status = status;
        this.accountDescription = accountDescription;
        this.accountType = accountType;
        this.currencyName = currencyName;
        this.userName = userName;
    }

    public void updateDynamicInfo(String accountName, BigDecimal balance, String status) {
        this.accountName = accountName;
        this.balance = balance;
        this.status = status;
    }

    public void updateSavingTargetAmount(Long savingTargetAmount) {
        this.savingTargetAmount = savingTargetAmount;
    }

    public void setAsPrimary() {
        this.isPrimary = true;
    }

    public void unsetPrimary() {
        this.isPrimary = false;
    }
}
