package com.ssafy.edu.awesomeproject.domain.fin.account.repository;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SavingsSettingRepository extends JpaRepository<SavingsSetting, Long> {
    Optional<SavingsSetting> findByUserIdAndIsActiveTrue(Long userId);

    List<SavingsSetting> findAllByIsActiveTrue();

    List<SavingsSetting> findAllByUserId(Long userId);

    void deleteAllByUserId(Long userId);
}
