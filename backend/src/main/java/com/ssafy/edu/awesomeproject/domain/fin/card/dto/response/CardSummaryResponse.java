package com.ssafy.edu.awesomeproject.domain.fin.card.dto.response;

import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
public class CardSummaryResponse {

    private boolean success;
    private String code;
    private String message;
    // 달 총 지출
    private Long totalAmount;

    private List<RankColum> RankColumList;

    @Getter
    @Builder
    public static class RankColum {

        private String categoryName;

        private double percentage;

        private int amount;
        private int amount_prv;
    }
}
