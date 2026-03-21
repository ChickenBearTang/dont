package com.ssafy.edu.awesomeproject.domain.ranking.event;

import com.ssafy.edu.awesomeproject.domain.ranking.service.RankingService;
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
        
        // TODO: [Task 4] SseEmitters를 주입받아 접속된 유저들에게 실시간 전파(send)하는 로직 추가 예정
    }
}
