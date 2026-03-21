package com.ssafy.edu.awesomeproject.domain.fin.consumption.repository;

import com.ssafy.edu.awesomeproject.domain.fin.consumption.entity.FinConsumptionMonthlyReport;
import java.time.LocalDate;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FinConsumptionMonthlyReportRepository
        extends JpaRepository<FinConsumptionMonthlyReport, Long> {
    Optional<FinConsumptionMonthlyReport> findTopByUserIdAndReportMonthAndIsLatestTrue(
            Long userId, LocalDate reportMonth);

    Optional<FinConsumptionMonthlyReport> findTopByUserIdAndReportMonthOrderByVersionNoDesc(
            Long userId, LocalDate reportMonth);
}
