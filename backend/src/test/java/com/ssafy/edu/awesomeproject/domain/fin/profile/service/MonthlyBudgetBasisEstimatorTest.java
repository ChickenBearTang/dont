package com.ssafy.edu.awesomeproject.domain.fin.profile.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.ssafy.edu.awesomeproject.domain.fin.profile.service.MonthlyBudgetBasisEstimator.Basis;
import com.ssafy.edu.awesomeproject.domain.fin.profile.service.MonthlyBudgetBasisEstimator.Entry;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class MonthlyBudgetBasisEstimatorTest {

    /** 2026-11-05 기준 관찰 구간은 2026-08-01 ~ 2026-10-31 (이번 달 제외). */
    private static final LocalDate TODAY = LocalDate.of(2026, 11, 5);

    private static Entry in(LocalDate date, long amount, String summary) {
        return new Entry(date, true, amount, summary, null, false);
    }

    private static Entry out(LocalDate date, long amount, String summary) {
        return new Entry(date, false, amount, summary, null, false);
    }

    private static List<Entry> month(int month, long salary, long rent, long phone) {
        return List.of(
                in(LocalDate.of(2026, month, 25), salary, "급여 입금"),
                out(LocalDate.of(2026, month, 1), rent, "월세"),
                out(LocalDate.of(2026, month, 15), phone, "통신비"));
    }

    private static List<Entry> concat(List<Entry>... groups) {
        List<Entry> all = new ArrayList<>();
        for (List<Entry> group : groups) {
            all.addAll(group);
        }
        return all;
    }

    @Test
    void windowIsTheLastThreeFullMonthsAndExcludesThisMonth() {
        assertThat(MonthlyBudgetBasisEstimator.windowStart(TODAY)).isEqualTo(LocalDate.of(2026, 8, 1));
        assertThat(MonthlyBudgetBasisEstimator.windowEnd(TODAY)).isEqualTo(LocalDate.of(2026, 10, 31));
        // 1월에는 구간이 해를 넘어간다.
        assertThat(MonthlyBudgetBasisEstimator.windowStart(LocalDate.of(2027, 1, 10)))
                .isEqualTo(LocalDate.of(2026, 10, 1));
        assertThat(MonthlyBudgetBasisEstimator.windowEnd(LocalDate.of(2027, 1, 10)))
                .isEqualTo(LocalDate.of(2026, 12, 31));
    }

    @Test
    void usesTheMedianOfTheObservedMonths() {
        List<Entry> entries =
                concat(
                        month(8, 2_600_000, 500_000, 50_000),
                        month(9, 2_600_000, 500_000, 50_000),
                        month(10, 2_600_000, 500_000, 50_000));

        Optional<Basis> basis = MonthlyBudgetBasisEstimator.estimate(entries, TODAY);

        assertThat(basis).contains(new Basis(2_600_000, 550_000, 3));
    }

    @Test
    void aOneOffLargeMonthDoesNotMoveTheMedian() {
        List<Entry> entries =
                concat(
                        month(8, 2_600_000, 500_000, 50_000),
                        month(9, 2_600_000, 500_000, 50_000),
                        // 10월에만 보너스 +5백만, 노트북 일시불 -2백만
                        month(10, 2_600_000, 500_000, 50_000),
                        List.of(
                                in(LocalDate.of(2026, 10, 28), 5_000_000, "성과급"),
                                out(LocalDate.of(2026, 10, 29), 2_000_000, "전자제품 결제")));

        Basis basis = MonthlyBudgetBasisEstimator.estimate(entries, TODAY).orElseThrow();

        assertThat(basis.monthlyIncome()).isEqualTo(2_600_000);
        assertThat(basis.monthlyFixedExpense()).isEqualTo(550_000);
    }

    @Test
    void evenNumberOfMonthsAveragesTheMiddlePair() {
        List<Entry> entries = concat(month(9, 2_000_000, 400_000, 0), month(10, 3_000_000, 600_000, 0));

        Basis basis = MonthlyBudgetBasisEstimator.estimate(entries, TODAY).orElseThrow();

        assertThat(basis.monthlyIncome()).isEqualTo(2_500_000);
        assertThat(basis.monthlyFixedExpense()).isEqualTo(500_000);
        assertThat(basis.observedMonths()).isEqualTo(2);
    }

    @Test
    void returnsNothingWhenNoIncomeWasObservedInsteadOfInventingValues() {
        // 지출만 있고 소득이 없는 구간, 이번 달 급여만 있는 경우 모두 추정하지 않는다.
        List<Entry> onlyExpenses = List.of(out(LocalDate.of(2026, 9, 1), 500_000, "월세"));
        List<Entry> onlyThisMonth = List.of(in(LocalDate.of(2026, 11, 1), 2_600_000, "급여 입금"));
        List<Entry> tooOld = List.of(in(LocalDate.of(2026, 7, 25), 2_600_000, "급여 입금"));

        assertThat(MonthlyBudgetBasisEstimator.estimate(List.of(), TODAY)).isEmpty();
        assertThat(MonthlyBudgetBasisEstimator.estimate(onlyExpenses, TODAY)).isEmpty();
        assertThat(MonthlyBudgetBasisEstimator.estimate(onlyThisMonth, TODAY)).isEmpty();
        assertThat(MonthlyBudgetBasisEstimator.estimate(tooOld, TODAY)).isEmpty();
    }

    @Test
    void internalTransfersAreNotIncome() {
        List<Entry> entries =
                List.of(
                        in(LocalDate.of(2026, 10, 25), 2_600_000, "급여 입금"),
                        // 세이브박스에서 꺼낸 돈, 시작 잔액 이월, 상대 계좌가 본인 계좌인 이체
                        in(LocalDate.of(2026, 10, 26), 300_000, "(세이브박스) 꺼내기"),
                        in(LocalDate.of(2026, 10, 1), 1_000_000, "(이월) 시작 잔액"),
                        new Entry(LocalDate.of(2026, 10, 27), true, 700_000, "이체", null, true));

        Basis basis = MonthlyBudgetBasisEstimator.estimate(entries, TODAY).orElseThrow();

        assertThat(basis.monthlyIncome()).isEqualTo(2_600_000);
    }

    @Test
    void cardBillsAndInvestmentsAreNotFixedExpenses() {
        List<Entry> entries =
                List.of(
                        in(LocalDate.of(2026, 10, 25), 2_600_000, "급여 입금"),
                        out(LocalDate.of(2026, 10, 1), 500_000, "월세"),
                        // 카드 거래에서 이미 변동 지출로 세는 돈, 5·3·2 의 3·2 구역
                        out(LocalDate.of(2026, 10, 10), 400_000, "카드대금 출금"),
                        out(LocalDate.of(2026, 10, 26), 700_000, "정기 이체(적금·투자)"),
                        new Entry(LocalDate.of(2026, 10, 12), false, 100_000, "이체", "ETF 주식 매수", false));

        Basis basis = MonthlyBudgetBasisEstimator.estimate(entries, TODAY).orElseThrow();

        assertThat(basis.monthlyFixedExpense()).isEqualTo(500_000);
    }

    @Test
    void autoSavingsCountsAsFixedExpenseButManualSavingsAndWithdrawalsDoNot() {
        List<Entry> entries =
                List.of(
                        in(LocalDate.of(2026, 10, 25), 2_600_000, "급여 입금"),
                        out(LocalDate.of(2026, 10, 1), 500_000, "월세"),
                        // 매달 쌓는 비상금은 '고정지출과 비상금을 포함한 5 구역'이다
                        out(LocalDate.of(2026, 10, 25), 200_000, "(자동저축) 출금"),
                        // 그때그때 옮긴 돈은 소비가 아니다
                        out(LocalDate.of(2026, 10, 28), 300_000, "(수동저축) 출금"),
                        out(LocalDate.of(2026, 10, 29), 50_000, "(세이브박스) 출금"));

        Basis basis = MonthlyBudgetBasisEstimator.estimate(entries, TODAY).orElseThrow();

        assertThat(basis.monthlyFixedExpense()).isEqualTo(700_000);
    }

    @Test
    void ignoresNonPositiveAmounts() {
        List<Entry> entries =
                List.of(
                        in(LocalDate.of(2026, 10, 25), 2_600_000, "급여 입금"),
                        in(LocalDate.of(2026, 10, 26), 0, "0원"),
                        out(LocalDate.of(2026, 10, 1), -500_000, "월세"));

        Basis basis = MonthlyBudgetBasisEstimator.estimate(entries, TODAY).orElseThrow();

        assertThat(basis).isEqualTo(new Basis(2_600_000, 0, 1));
    }
}
