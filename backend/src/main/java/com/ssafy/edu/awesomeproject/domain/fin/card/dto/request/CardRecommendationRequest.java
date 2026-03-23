package com.ssafy.edu.awesomeproject.domain.fin.card.dto.request;

import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class CardRecommendationRequest {
    private String user_name;
    private String month;
    private List<TransactionDto> raw_data;

    @Getter
    @Builder
    public static class TransactionDto {
        private String storeName;
        private Long amount;
        private String category;
    }
}
