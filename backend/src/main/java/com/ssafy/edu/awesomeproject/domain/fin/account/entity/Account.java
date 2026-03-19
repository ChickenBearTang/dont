package com.ssafy.edu.awesomeproject.domain.fin.account.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDate;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "accounts")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class Account extends BaseEntity {

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

    @Enumerated(EnumType.STRING)
    @Column(name = "account_role", nullable = false, length = 20)
    private AccountRole accountRole;

    @Column(name = "is_primary", nullable = false)
    private boolean isPrimary;

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
    private BigDecimal balance;

    @Column(name = "last_transaction_date")
    private LocalDate lastTransactionDate;

    @Column(name = "currency_code", length = 10)
    private String currencyCode;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private AccountStatus status;

    @Column(name = "user_name", length = 100)
    private String userName;

    @Builder
    public Account(
            Long userId,
            String accountNo,
            String bankCode,
            String bankName,
            AccountRole accountRole,
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
            AccountStatus status,
            String userName) {
        this.userId = userId;
        this.accountNo = accountNo;
        this.bankCode = bankCode;
        this.bankName = bankName;
        this.accountRole = accountRole;
        this.isPrimary = isPrimary;
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
        this.userName = userName;
    }

    public void updateDynamicInfo(String accountName, BigDecimal balance, AccountStatus status) {
        this.accountName = accountName;
        this.balance = balance;
        this.status = status;
    }

    public void setAsPrimary() {
        this.isPrimary = true;
    }

    public void unsetPrimary() {
        this.isPrimary = false;
    }
}
