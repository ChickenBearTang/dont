package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Report;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReportStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReportTargetType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReportRepository extends JpaRepository<Report, Long> {
    boolean existsByReporterUserIdAndTargetTypeAndTargetId(
            Long reporterUserId, ReportTargetType targetType, Long targetId);

    Page<Report> findByReportStatusOrderByIdDesc(ReportStatus reportStatus, Pageable pageable);

    Page<Report> findAllByOrderByIdDesc(Pageable pageable);
}
