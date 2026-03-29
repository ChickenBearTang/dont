package com.ssafy.edu.awesomeproject.domain.fin.card.dto.response;

import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class CardListResponse {

    private boolean success;
    private String code;
    private String message;
    private List<CardItem> cards;

    @Getter
    @Builder
    public static class CardItem {

        private Long id;
        private String cardIssuerName;
        private String cardName;


        private long monthlyCardExpense;
    }
}
