package com.ssafy.edu.awesomeproject.domain.fin.consumption.repository;

import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.FinConsumptionJustification;
import java.time.LocalDate;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FinConsumptionJustificationRepository
        extends JpaRepository<FinConsumptionJustification, Long> {
    List<FinConsumptionJustification> findAllByUserIdAndTargetMonthOrderByCreatedAtDesc(
            Long userId, LocalDate targetMonth);
}
