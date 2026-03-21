package com.ssafy.edu.awesomeproject.domain.ranking.event;

import com.ssafy.edu.awesomeproject.domain.ranking.service.RankingService;
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

    /**
     * 저축 DB 커밋이 완벽히 완료된 이후에 비동기적으로 랭킹 업데이트 이벤트를 수신합니다.
     */
    @Async("rankingTaskExecutor")
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleBalanceUpdate(SaveboxBalanceUpdatedEvent event) {
        log.info("[Ranking Update Event] User: {}, New Balance: {}, Cohort: {}", 
                 event.userId(), event.currentBalance(), event.cohort());
        
        // Redis ZSET에 업데이트 (전체 & 기수별)
        rankingService.updateSaveboxRanking(event.userId(), event.currentBalance(), event.cohort());
        
        // 인메모리에 붙어 있는 모든 유저 클라이언트들에게 랭킹 변동 알림(SSE) 브로드캐스트 직파!
        sseEmitters.sendRankingUpdateNotification(event.userId());
    }
}
