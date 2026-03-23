package com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request;

import com.ssafy.edu.awesomeproject.domain.fin.card.dto.request.AiAnalysisRequest;
import java.util.List;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class StrictSecretaryRequest {
    private AiAnalysisRequest.UserProfileBase user_profile;
    private String item_text;
    private String item_link;
    private String user_reason;
    private List<AiAnalysisRequest.CardTransactionBase> recent_transactions;
    private String ai_report_context;
}
