package com.ssafy.edu.awesomeproject.domain.fin.profile.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.ledger.LedgerSummaries;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

/**
 * 계좌 거래에서 월 소득과 월 고정지출을 추정한다 (5·3·2 예산 규칙의 입력).
 *
 * <p>DB 에 소득/고정지출 열이 없어서 입출금 계좌의 입출금 내역에서 거꾸로 읽는다. 읽은 값은 "추정"이므로 호출하는 쪽이
 * isEstimated 로 표시해서 AI 에 넘긴다.
 *
 * <p>규칙
 *
 * <ul>
 *   <li>관찰 구간은 이번 달을 뺀 최근 3개월(완전한 달)이다. 이번 달은 아직 급여가 안 들어왔을 수 있다.
 *   <li>소득 = 그 달에 입출금 계좌로 들어온 돈 중 본인 계좌 이동(자동저축, 꺼내기, 이월)이 아닌 것의 합.
 *   <li>고정지출 = 그 달에 입출금 계좌에서 나간 돈 중 카드대금(카드 거래에서 이미 변동 지출로 세므로 겹침),
 *       투자·적금(5·3·2 의 3과 2 구역), 본인 계좌 이동을 뺀 것의 합. 단 매달 쌓는 자동저축은 비상금이라 고정지출에
 *       넣는다 ("고정지출과 비상금을 포함한 5 구역").
 *   <li>소득이 있었던 달만 관찰한 달로 센다. 그 달들의 값의 중앙값을 쓴다 (한 달의 큰 일회성 지출/입금에 흔들리지
 *       않게). 관찰한 달이 없으면 추정하지 않는다 (아무 값도 만들어 내지 않는다).
 * </ul>
 */
public final class MonthlyBudgetBasisEstimator {

    public static final int WINDOW_MONTHS = 3;
    public static final String METHOD = "median_of_last_3_full_months";

    private static final List<String> INVESTMENT_KEYWORDS = List.of("적금", "투자", "펀드", "주식", "연금");

    private MonthlyBudgetBasisEstimator() {}

    /**
     * 입출금 계좌 거래 한 건.
     *
     * @param deposit true 면 입금, false 면 출금
     * @param internalTransfer 상대 계좌가 본인 계좌인 이체
     */
    public record Entry(
            LocalDate date,
            boolean deposit,
            long amount,
            String summary,
            String memo,
            boolean internalTransfer) {}

    public record Basis(long monthlyIncome, long monthlyFixedExpense, int observedMonths) {}

    /** 관찰 구간의 첫날 (이번 달에서 3개월 전 1일). */
    public static LocalDate windowStart(LocalDate today) {
        return YearMonth.from(today).minusMonths(WINDOW_MONTHS).atDay(1);
    }

    /** 관찰 구간의 마지막 날 (지난달 말일). */
    public static LocalDate windowEnd(LocalDate today) {
        return YearMonth.from(today).minusMonths(1).atEndOfMonth();
    }

    public static Optional<Basis> estimate(Collection<Entry> entries, LocalDate today) {
        YearMonth current = YearMonth.from(today);
        List<Long> incomes = new ArrayList<>();
        List<Long> fixedExpenses = new ArrayList<>();

        for (int back = 1; back <= WINDOW_MONTHS; back++) {
            YearMonth month = current.minusMonths(back);
            long income = 0L;
            long fixed = 0L;
            for (Entry entry : entries) {
                if (entry.amount() <= 0 || !YearMonth.from(entry.date()).equals(month)) {
                    continue;
                }
                if (entry.deposit()) {
                    if (!isInternal(entry)) {
                        income += entry.amount();
                    }
                } else if (countsAsFixedExpense(entry)) {
                    fixed += entry.amount();
                }
            }
            if (income > 0) {
                incomes.add(income);
                fixedExpenses.add(fixed);
            }
        }
        if (incomes.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(new Basis(median(incomes), median(fixedExpenses), incomes.size()));
    }

    static boolean isInternal(Entry entry) {
        return entry.internalTransfer() || LedgerSummaries.isInternal(entry.summary());
    }

    static boolean countsAsFixedExpense(Entry entry) {
        if (LedgerSummaries.isAutoSavings(entry.summary())) {
            return true; // 매달 쌓는 비상금
        }
        if (isInternal(entry) || isCardBill(entry) || isInvestment(entry)) {
            return false;
        }
        return true;
    }

    /** AI 쪽 월 지출 계산(consumption db.py 의 _account_category)과 같은 기준이다. */
    static boolean isCardBill(Entry entry) {
        String text = text(entry);
        return text.contains("카드") && text.contains("대금");
    }

    static boolean isInvestment(Entry entry) {
        String text = text(entry);
        return INVESTMENT_KEYWORDS.stream().anyMatch(text::contains);
    }

    private static String text(Entry entry) {
        return (entry.summary() == null ? "" : entry.summary())
                + " "
                + (entry.memo() == null ? "" : entry.memo());
    }

    /** 짝수 개면 가운데 두 값의 평균(원 미만 버림). */
    static long median(List<Long> values) {
        List<Long> sorted = new ArrayList<>(values);
        Collections.sort(sorted);
        int size = sorted.size();
        if (size % 2 == 1) {
            return sorted.get(size / 2);
        }
        return (sorted.get(size / 2 - 1) + sorted.get(size / 2)) / 2;
    }
}
