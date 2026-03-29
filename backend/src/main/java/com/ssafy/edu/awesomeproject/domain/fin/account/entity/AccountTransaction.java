package com.ssafy.edu.awesomeproject.domain.fin.account.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "account_transactions")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class AccountTransaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
    }

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "account_id", nullable = false)
    private Account account;

    @Column(name = "transaction_unique_no", unique = true, nullable = false, length = 30)
    private String transactionUniqueNo;

    @Column(name = "transaction_date", nullable = false)
    private LocalDate transactionDate;

    @Column(name = "transaction_time", nullable = false, length = 10)
    private String transactionTime;

    @Column(name = "transaction_type", nullable = false, length = 10)
    private String transactionType;

    @Column(name = "transaction_type_name", length = 30)
    private String transactionTypeName;

    @Column(name = "transaction_account_no", length = 30)
    private String transactionAccountNo;

    @Column(name = "transaction_amount", nullable = false, precision = 15, scale = 2)
    private BigDecimal transactionAmount;

    @Column(name = "after_balance", nullable = false, precision = 15, scale = 2)
    private BigDecimal afterBalance;

    @Column(name = "transaction_summary", length = 200)
    private String transactionSummary;

    @Column(name = "transaction_memo", length = 500)
    private String transactionMemo;

    @Column(name = "auto_savings_processed", nullable = false)
    private boolean autoSavingsProcessed = false;

    @Builder
    public AccountTransaction(
        Account account,
        String transactionUniqueNo,
        LocalDate transactionDate,
        String transactionTime,
        String transactionType,
        String transactionTypeName,
        String transactionAccountNo,
        BigDecimal transactionAmount,
        BigDecimal afterBalance,
        String transactionSummary,
        String transactionMemo) {
        this.account = account;
        this.transactionUniqueNo = transactionUniqueNo;
        this.transactionDate = transactionDate;
        this.transactionTime = transactionTime;
        this.transactionType = transactionType;
        this.transactionTypeName = transactionTypeName;
        this.transactionAccountNo = transactionAccountNo;
        this.transactionAmount = transactionAmount;
        this.afterBalance = afterBalance;
        this.transactionSummary = transactionSummary;
        this.transactionMemo = transactionMemo;
    }

    public void markAutoSavingsProcessed() {
        this.autoSavingsProcessed = true;
    }
}
