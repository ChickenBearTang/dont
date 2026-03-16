package com.ssafy.edu.awesomeproject.domain.fin.account.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class Account {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long userId;

    @Column(unique = true, nullable = false)
    private String accountNo;

    @Column(nullable = false)
    private String bankName;

    // 🌟 추가: 은행 코드 (e.g. "001")
    private String bankCode;

    private String accountName;

    private Long balance;

    // 🌟 추가: 통화 (e.g. "KRW")
    private String currency;

    private boolean isMainAccount;

    private Long savingTargetAmount;

    @Builder
    public Account(Long userId, String accountNo, String bankName, String bankCode, String accountName, String currency) {
        this.userId = userId;
        this.accountNo = accountNo;
        this.bankName = bankName;
        this.bankCode = bankCode;
        this.accountName = accountName;
        this.currency = currency;
    }

    // 정보 업데이트를 위한 비즈니스 메서드
    public void updateInfo(String accountName, Long balance, String currency) {
        this.accountName = accountName;
        this.balance = balance;
        this.currency = currency;
    }
}