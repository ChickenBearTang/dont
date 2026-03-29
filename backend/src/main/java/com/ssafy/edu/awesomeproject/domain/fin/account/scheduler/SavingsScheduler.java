package com.ssafy.edu.awesomeproject.domain.fin.account.scheduler;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.service.AccountService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class SavingsScheduler {

    private final SavingsSettingRepository savingsSettingRepository;
    private final AccountService accountService;


    @Scheduled(fixedDelay = 3600000)
    public void scheduleAutomaticSavings() {
        log.info("--- [Background] 자동 저축 스케줄러 시작 ---");

        List<SavingsSetting> activeSettings = savingsSettingRepository.findAllByIsActiveTrue();
        log.info("감지된 활성 자동 저축 설정 수: {}", activeSettings.size());

        for (SavingsSetting setting : activeSettings) {
            try {
                log.info("사용자(ID: {})에 대한 동기화 및 자동저축 검토 중...", setting.getUserId());
                accountService.refreshAccountList(setting.getUserId());
            } catch (Exception e) {
                log.error("사용자 {}의 자동 저축 동기화 중 오류 발생: {}",
                        setting.getUserId(), e.getMessage());
            }
        }

        log.info("--- [Background] 자동 저축 스케줄러 완료 ---");
    }
}
