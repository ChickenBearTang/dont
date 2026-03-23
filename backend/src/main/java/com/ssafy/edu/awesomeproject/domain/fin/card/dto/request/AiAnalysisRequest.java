package com.ssafy.edu.awesomeproject.domain.fin.card.dto.request;

import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class AiAnalysisRequest {
    private UserProfileBase user_profile;
    private List<CardTransactionBase> card_transactions;
    private List<AccountTransactionBase> account_transactions;
    private String start_date;
    private String end_date;
    private boolean include_ai;

    @Getter
    @Builder
    public static class UserProfileBase {
        private String user_id;
        private String name;
        private long monthly_income;
    }

    @Getter
    @Builder
    public static class CardTransactionBase {
        private String transaction_date;
        private String transaction_time;
        private String merchant_name;
        private String category_name;
        private long transaction_amount;
        private String transaction_type;
        private String approval_no;
        private String description;
    }

    @Getter
    @Builder
    public static class AccountTransactionBase {
        private String transaction_date;
        private String transaction_time;
        private String transaction_type;
        private String transaction_type_name;
        private long transaction_amount;
        private long after_balance;
        private String transaction_summary;
        private String transaction_memo;
    }
}
