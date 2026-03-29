package com.ssafy.edu.awesomeproject.domain.ranking.event;

import com.ssafy.edu.awesomeproject.domain.ranking.dto.response.RankingListResponse;
import com.ssafy.edu.awesomeproject.domain.ranking.service.RankingService;
import com.ssafy.edu.awesomeproject.domain.ranking.sse.RankingUpdatePayload;
import com.ssafy.edu.awesomeproject.domain.ranking.sse.SseEmitters;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Slf4j
@Component
@RequiredArgsConstructor
public class RankingEventListener {

    private final RankingService rankingService;
    private final SseEmitters sseEmitters;


    @Async("rankingTaskExecutor")
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleBalanceUpdate(SaveboxBalanceUpdatedEvent event) {
        log.info(
                "[Ranking Update Event] User: {}, New Balance: {}, Cohort: {}",
                event.userId(),
                event.currentBalance(),
                event.cohort());


        rankingService.updateSaveboxRanking(event.userId(), event.currentBalance(), event.cohort());


        RankingListResponse totalRankingData =
                RankingListResponse.of(
                        rankingService.getTop100Ranking(null),
                        rankingService.getMyRanking(event.userId(), null));


        RankingUpdatePayload payload = new RankingUpdatePayload(event.userId(), totalRankingData);
        sseEmitters.sendRankingUpdateNotification(payload);
    }
}
