package com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record StrictSecretaryEvaluateRequest(
        @JsonProperty("user_profile") UserProfile userProfile,
        @JsonProperty("item_text") String itemText,
        @JsonProperty("item_link") String itemLink,
        @JsonProperty("user_reason") String userReason,
        @JsonProperty("recent_transactions") List<RecentTransaction> recentTransactions,
        @JsonProperty("ai_report_context") String aiReportContext) {

    public record UserProfile(
            @JsonProperty("user_id") String userId,
            @JsonProperty("name") String name,
            @JsonProperty("monthly_income") int monthlyIncome) {}

    public record RecentTransaction(
            @JsonProperty("transaction_date") String transactionDate,
            @JsonProperty("transaction_time") String transactionTime,
            @JsonProperty("merchant_name") String merchantName,
            @JsonProperty("category_name") String categoryName,
            @JsonProperty("transaction_amount") int transactionAmount,
            @JsonProperty("transaction_type") String transactionType,
            @JsonProperty("approval_no") String approvalNo,
            @JsonProperty("description") String description) {}
}
