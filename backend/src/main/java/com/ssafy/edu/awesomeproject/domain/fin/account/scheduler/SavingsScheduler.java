package com.ssafy.edu.awesomeproject.domain.fin.account.scheduler;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.AccountService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 밀린 자동저축을 처리한다. 입금 직후에는 바로 처리되지만, 그때 주계좌 잔액이 저축액보다 적어 미뤄진 건이나 DB 에 직접
 * 들어온 입금은 이 스케줄러가 한 시간마다 다시 시도한다. 외부 호출은 없다.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SavingsScheduler {

    private final SavingsSettingRepository savingsSettingRepository;
    private final AccountService accountService;

    @Scheduled(fixedDelay = 3600000)
    public void scheduleAutomaticSavings() {
        List<SavingsSetting> activeSettings = savingsSettingRepository.findAllByIsActiveTrue();
        log.info("자동 저축 스케줄러 시작 - 활성 규칙 {}건", activeSettings.size());

        for (SavingsSetting setting : activeSettings) {
            try {
                accountService.processPendingAutoSavings(setting.getUserId());
            } catch (Exception e) {
                log.error("사용자 {}의 밀린 자동저축 처리 중 오류: {}", setting.getUserId(), e.getMessage());
            }
        }
    }
}
