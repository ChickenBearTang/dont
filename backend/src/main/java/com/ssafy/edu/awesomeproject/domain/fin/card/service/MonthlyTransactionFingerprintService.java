package com.ssafy.edu.awesomeproject.domain.fin.card.service;

import com.ssafy.edu.awesomeproject.domain.fin.card.repository.CardTransactionRepository;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.HexFormat;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class MonthlyTransactionFingerprintService {

    private static final String EMPTY_FINGERPRINT = "empty";
    private final CardTransactionRepository cardTransactionRepository;

    public String buildMonthlyFingerprint(Long userId, YearMonth yearMonth) {
        LocalDate startDate = yearMonth.atDay(1);
        LocalDate endDate = yearMonth.atEndOfMonth();
        return buildMonthlyFingerprint(userId, startDate, endDate);
    }

    public String buildMonthlyFingerprint(Long userId, LocalDate reportMonthStartDate) {
        YearMonth yearMonth = YearMonth.from(reportMonthStartDate);
        return buildMonthlyFingerprint(userId, yearMonth.atDay(1), yearMonth.atEndOfMonth());
    }

    private String buildMonthlyFingerprint(Long userId, LocalDate startDate, LocalDate endDate) {
        List<CardTransactionRepository.MonthlyTransactionFingerprintProjection> transactions =
                cardTransactionRepository.findMonthlyTransactionsForFingerprint(
                        userId, startDate, endDate);
        if (transactions.isEmpty()) {
            return EMPTY_FINGERPRINT;
        }

        StringBuilder builder = new StringBuilder(transactions.size() * 64);
        for (CardTransactionRepository.MonthlyTransactionFingerprintProjection tx : transactions) {
            builder.append(nullToDash(tx.getId()))
                    .append('|')
                    .append(nullToDash(tx.getTransactionDate()))
                    .append('|')
                    .append(nullToDash(tx.getTransactionTime()))
                    .append('|')
                    .append(nullToDash(tx.getTransactionAmount()))
                    .append('|')
                    .append(nullToDash(tx.getMerchantName()))
                    .append('|')
                    .append(nullToDash(tx.getCategoryName()))
                    .append('\n');
        }
        return sha256Hex(builder.toString());
    }

    private String nullToDash(Object value) {
        return value == null ? "-" : String.valueOf(value);
    }

    private String sha256Hex(String source) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(source.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 algorithm not available", exception);
        }
    }
}
