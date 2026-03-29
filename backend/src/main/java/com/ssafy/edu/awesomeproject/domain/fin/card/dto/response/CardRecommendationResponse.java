package com.ssafy.edu.awesomeproject.domain.fin.card.dto.response;

import java.util.Map;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CardRecommendationResponse {
    private PersonaDto user_persona;
    private CardResultDto best_card;
    private List<CardResultDto> all_cards;
    private Long total_spend;
    private Map<String, Long> type_spend_stats;

    @Getter
    @Setter
    public static class PersonaDto {
        private String type_id;
        private String name;
        private String nickname;
        private String description;
        private Long total_amount;
        private Long count;
        private Long score;
    }

    @Getter
    @Setter
    public static class CardResultDto {
        private String card_id;
        private String name;
        private String main_text;
        private List<String> sub_text;
        private List<StructuredBenefitDto> structured_benefits;
        private Long estimated_savings;
        private Double picking_rate;
        private String comment;
    }

    @Getter
    @Setter
    public static class StructuredBenefitDto {
        private String target_type;
        private String type;
        private Double rate;
    }
}
