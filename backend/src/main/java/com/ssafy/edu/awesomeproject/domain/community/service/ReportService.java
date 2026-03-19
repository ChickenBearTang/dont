package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.community.dto.request.ReportCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.ReportProcessRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.AdminReportDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.AdminReportListResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.ReportCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.ReportProcessResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Comment;
import com.ssafy.edu.awesomeproject.domain.community.entity.CommentStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.Report;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReportReasonCode;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReportStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReportTargetType;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.CommentRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.ReportRepository;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class ReportService {
    private final ReportRepository reportRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;

    public ReportService(
            ReportRepository reportRepository,
            PostRepository postRepository,
            CommentRepository commentRepository) {
        this.reportRepository = reportRepository;
        this.postRepository = postRepository;
        this.commentRepository = commentRepository;
    }

    @Transactional
    public ReportCreateResponseDto create(Long reporterUserId, ReportCreateRequestDto requestDto) {
        validateOtherReasonDetail(requestDto.reasonCode(), requestDto.detailText());
        validateDuplicateReport(reporterUserId, requestDto.targetType(), requestDto.targetId());

        Long targetAuthorId = resolveTargetAuthorId(requestDto.targetType(), requestDto.targetId());
        if (targetAuthorId.equals(reporterUserId)) {
            throw new CommunityException(CommunityErrorCode.SELF_REPORT_NOT_ALLOWED);
        }

        Report report =
                reportRepository.save(
                        new Report(
                                reporterUserId,
                                requestDto.targetType(),
                                requestDto.targetId(),
                                requestDto.reasonCode(),
                                requestDto.detailText()));

        return new ReportCreateResponseDto(
                report.getId(), report.getReportStatus().name(), report.getCreatedAt());
    }

    private void validateOtherReasonDetail(ReportReasonCode reasonCode, String detailText) {
        if (reasonCode == ReportReasonCode.OTHER && (detailText == null || detailText.isBlank())) {
            throw new CommunityException(CommunityErrorCode.INVALID_INPUT);
        }
    }

    private void validateDuplicateReport(
            Long reporterUserId, ReportTargetType targetType, Long targetId) {
        if (reportRepository.existsByReporterUserIdAndTargetTypeAndTargetId(
                reporterUserId, targetType, targetId)) {
            throw new CommunityException(CommunityErrorCode.REPORT_ALREADY_EXISTS);
        }
    }

    private Long resolveTargetAuthorId(ReportTargetType targetType, Long targetId) {
        if (targetType == ReportTargetType.POST) {
            Post post =
                    postRepository
                            .findByIdAndStatus(targetId, PostStatus.ACTIVE)
                            .orElseThrow(
                                    () ->
                                            new CommunityException(
                                                    CommunityErrorCode.REPORT_TARGET_NOT_FOUND));
            return post.getUser().getId();
        }

        Comment comment =
                commentRepository
                        .findByIdAndStatus(targetId, CommentStatus.ACTIVE)
                        .orElseThrow(
                                () ->
                                        new CommunityException(
                                                CommunityErrorCode.REPORT_TARGET_NOT_FOUND));
        return comment.getUser().getId();
    }

    public AdminReportListResponseDto getReportsForAdmin(
            ReportStatus status, Integer page, Integer size) {
        int pageNumber = (page == null || page < 0) ? 0 : page;
        int pageSize = (size == null || size <= 0) ? 20 : size;

        PageRequest pageRequest =
                PageRequest.of(pageNumber, pageSize, Sort.by(Sort.Direction.DESC, "id"));
        Page<Report> reportPage =
                status == null
                        ? reportRepository.findAllByOrderByIdDesc(pageRequest)
                        : reportRepository.findByReportStatusOrderByIdDesc(status, pageRequest);

        List<AdminReportListResponseDto.ReportSummaryDto> content =
                reportPage.getContent().stream()
                        .map(
                                report ->
                                        new AdminReportListResponseDto.ReportSummaryDto(
                                                report.getId(),
                                                report.getReporterUserId(),
                                                report.getTargetType().name(),
                                                report.getTargetId(),
                                                report.getReasonCode().name(),
                                                report.getReportStatus().name(),
                                                report.getCreatedAt(),
                                                report.getProcessedAt()))
                        .toList();

        return new AdminReportListResponseDto(
                content,
                reportPage.getNumber(),
                reportPage.getSize(),
                reportPage.getTotalElements(),
                reportPage.getTotalPages(),
                reportPage.hasNext());
    }

    public AdminReportDetailResponseDto getReportDetailForAdmin(Long reportId) {
        Report report = getReport(reportId);
        return new AdminReportDetailResponseDto(
                report.getId(),
                report.getReporterUserId(),
                report.getTargetType().name(),
                report.getTargetId(),
                report.getReasonCode().name(),
                report.getDetailText(),
                report.getReportStatus().name(),
                report.getProcessedByUserId(),
                report.getProcessNote(),
                report.getProcessedAt(),
                report.getCreatedAt(),
                report.getUpdatedAt());
    }

    @Transactional
    public ReportProcessResponseDto blind(
            Long reportId, Long adminUserId, ReportProcessRequestDto requestDto) {
        Report report = getReport(reportId);
        validateNotProcessed(report);
        report.blind(adminUserId, requestDto.processNote());
        return toProcessResponse(report);
    }

    @Transactional
    public ReportProcessResponseDto reject(
            Long reportId, Long adminUserId, ReportProcessRequestDto requestDto) {
        Report report = getReport(reportId);
        validateNotProcessed(report);
        report.reject(adminUserId, requestDto.processNote());
        return toProcessResponse(report);
    }

    private Report getReport(Long reportId) {
        return reportRepository
                .findById(reportId)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.REPORT_NOT_FOUND));
    }

    private void validateNotProcessed(Report report) {
        if (report.getReportStatus() != ReportStatus.RECEIVED) {
            throw new CommunityException(CommunityErrorCode.REPORT_ALREADY_PROCESSED);
        }
    }

    private ReportProcessResponseDto toProcessResponse(Report report) {
        return new ReportProcessResponseDto(
                report.getId(),
                report.getReportStatus().name(),
                report.getProcessedByUserId(),
                report.getProcessNote(),
                report.getProcessedAt());
    }
}
