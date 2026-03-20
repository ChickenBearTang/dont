package com.ssafy.edu.awesomeproject.domain.fin.card.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Entity
@Table(name = "cards")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Card extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "card_no", nullable = false, length = 64)
    private String cardNo;

    @Column(name = "cvc", nullable = false, length = 8)
    private String cvc;

    @Column(name = "card_unique_no", length = 128)
    private String cardUniqueNo;

    @Column(name = "card_issuer_code", length = 32)
    private String cardIssuerCode;

    @Column(name = "card_issuer_name", length = 128)
    private String cardIssuerName;

    @Column(name = "card_name", length = 128)
    private String cardName;

    @Column(name = "card_description", length = 255)
    private String cardDescription;

    @Column(name = "baseline_performance")
    private Long baselinePerformance;

    @Column(name = "max_benefit_limit")
    private Long maxBenefitLimit;

    @Column(name = "card_expiry_date", length = 32)
    private String cardExpiryDate;

    @Column(name = "withdrawal_account_no", length = 64)
    private String withdrawalAccountNo;

    @Column(name = "withdrawal_date", length = 32)
    private String withdrawalDate;

    @Builder
    public Card(
            User user,
            String cardNo,
            String cvc,
            String cardUniqueNo,
            String cardIssuerCode,
            String cardIssuerName,
            String cardName,
            String cardDescription,
            Long baselinePerformance,
            Long maxBenefitLimit,
            String cardExpiryDate,
            String withdrawalAccountNo,
            String withdrawalDate) {
        this.user = user;
        this.cardNo = cardNo;
        this.cvc = cvc;
        this.cardUniqueNo = cardUniqueNo;
        this.cardIssuerCode = cardIssuerCode;
        this.cardIssuerName = cardIssuerName;
        this.cardName = cardName;
        this.cardDescription = cardDescription;
        this.baselinePerformance = baselinePerformance;
        this.maxBenefitLimit = maxBenefitLimit;
        this.cardExpiryDate = cardExpiryDate;
        this.withdrawalAccountNo = withdrawalAccountNo;
        this.withdrawalDate = withdrawalDate;
    }

    public void updateFromExternal(
            String cardNo,
            String cvc,
            String cardIssuerCode,
            String cardIssuerName,
            String cardName,
            String cardDescription,
            Long baselinePerformance,
            Long maxBenefitLimit,
            String cardExpiryDate,
            String withdrawalAccountNo,
            String withdrawalDate) {
        this.cardNo = cardNo;
        this.cvc = cvc;
        this.cardIssuerCode = cardIssuerCode;
        this.cardIssuerName = cardIssuerName;
        this.cardName = cardName;
        this.cardDescription = cardDescription;
        this.baselinePerformance = baselinePerformance;
        this.maxBenefitLimit = maxBenefitLimit;
        this.cardExpiryDate = cardExpiryDate;
        this.withdrawalAccountNo = withdrawalAccountNo;
        this.withdrawalDate = withdrawalDate;
    }
}
