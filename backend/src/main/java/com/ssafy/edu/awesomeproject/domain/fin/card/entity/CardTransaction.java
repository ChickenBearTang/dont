package com.ssafy.edu.awesomeproject.domain.fin.card.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalDate;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Entity
@Table(name = "card_transactions")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class CardTransaction extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "card_id", nullable = false)
    private Card card;

    @Column(name = "transaction_date", nullable = false)
    private LocalDate transactionDate;

    @Column(name = "transaction_time", length = 16)
    private String transactionTime;

    @Column(name = "merchant_name", length = 255)
    private String merchantName;

    @Column(name = "category_name", length = 128)
    private String categoryName;

    @Column(name = "transaction_amount")
    private Long transactionAmount;

    @Column(name = "transaction_type", length = 64)
    private String transactionType;

    @Column(name = "approval_no", length = 64)
    private String approvalNo;

    @Column(name = "description", length = 500)
    private String description;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Builder
    public CardTransaction(
            Card card,
            LocalDate transactionDate,
            String transactionTime,
            String merchantName,
            String categoryName,
            Long transactionAmount,
            String transactionType,
            String approvalNo,
            String description,
            Long userId) {
        this.card = card;
        this.transactionDate = transactionDate;
        this.transactionTime = transactionTime;
        this.merchantName = merchantName;
        this.categoryName = categoryName;
        this.transactionAmount = transactionAmount;
        this.transactionType = transactionType;
        this.approvalNo = approvalNo;
        this.description = description;
        this.userId = userId;
    }
}


