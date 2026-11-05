package com.ssafy.edu.awesomeproject.domain.fin.account.ledger;

import java.util.List;

/**
 * 원장이 거래 내역의 적요(summary)에 남기는 문구.
 *
 * <p>본인 계좌 사이를 오가는 돈은 소득도 지출도 아니다. 재무 프로필(소득·고정지출 추정)과 AI 쪽 월 소득
 * 추정이 이 적요 접두어로 그런 거래를 걸러내므로, 문구를 바꾸면 그 두 곳도 함께 확인해야 한다.
 */
public final class LedgerSummaries {

    public static final String AUTO_SAVINGS_OUT = "(자동저축) 출금";
    public static final String AUTO_SAVINGS_IN = "(자동저축) 입금";
    public static final String MANUAL_SAVINGS_OUT = "(수동저축) 출금";
    public static final String MANUAL_SAVINGS_IN = "(수동저축) 입금";
    public static final String SAVEBOX_WITHDRAW_OUT = "(세이브박스) 출금";
    public static final String SAVEBOX_WITHDRAW_IN = "(세이브박스) 꺼내기";

    private static final String AUTO_SAVINGS_PREFIX = "(자동저축)";

    /** 본인 계좌 사이 이동이라 소득·지출로 세지 않는 거래의 접두어. "(이월)"은 시작 잔액 입금이다. */
    public static final List<String> INTERNAL_PREFIXES =
            List.of(AUTO_SAVINGS_PREFIX, "(수동저축)", "(세이브박스)", "(이월)");

    private LedgerSummaries() {}

    public static boolean isInternal(String summary) {
        if (summary == null) {
            return false;
        }
        String trimmed = summary.strip();
        return INTERNAL_PREFIXES.stream().anyMatch(trimmed::startsWith);
    }

    /** 매달 쌓는 비상금. 5·3·2 규칙에서는 생활비(5) 구역의 고정지출에 포함해서 센다. */
    public static boolean isAutoSavings(String summary) {
        return summary != null && summary.strip().startsWith(AUTO_SAVINGS_PREFIX);
    }
}
