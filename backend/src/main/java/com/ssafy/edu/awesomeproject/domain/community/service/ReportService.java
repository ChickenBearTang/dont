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
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReportService {
    private final ReportRepository reportRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;
    private final NotificationService notificationService;

    public ReportService(
        ReportRepository reportRepository,
        PostRepository postRepository,
        CommentRepository commentRepository,
        NotificationService notificationService) {
        this.reportRepository = reportRepository;
        this.postRepository = postRepository;
        this.commentRepository = commentRepository;
        this.notificationService = notificationService;
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

        sendReportReceivedNotification(report, targetAuthorId);

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

    @Transactional(readOnly = true)
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

    @Transactional(readOnly = true)
    public AdminReportDetailResponseDto getReportDetailForAdmin(Long reportId) {
        Report report = getReport(reportId);
        if (report.getTargetType() == ReportTargetType.POST) {
            Post post =
                postRepository
                    .findById(report.getTargetId())
                    .orElseThrow(
                        () ->
                            new CommunityException(
                                CommunityErrorCode.REPORT_TARGET_NOT_FOUND));

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
                report.getUpdatedAt(),
                post.getUser().getNickname(),
                post.getTitle(),
                post.getContent(),
                post.getStatus().name(),
                post.getId());
        }

        Comment comment =
            commentRepository
                .findById(report.getTargetId())
                .orElseThrow(
                    () ->
                        new CommunityException(
                            CommunityErrorCode.REPORT_TARGET_NOT_FOUND));

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
            report.getUpdatedAt(),
            comment.getUser().getNickname(),
            null,
            comment.getContent(),
            comment.getStatus().name(),
            comment.getPost().getId());
    }

    @Transactional
    public ReportProcessResponseDto blind(
        Long reportId, Long adminUserId, ReportProcessRequestDto requestDto) {
        Report report = getReport(reportId);
        validateNotProcessed(report);

        blindTarget(report);

        report.blind(adminUserId, requestDto.processNote());
        reportRepository.save(report);

        sendReportProcessedNotification(report);

        return toProcessResponse(report);
    }

    @Transactional
    public ReportProcessResponseDto reject(
        Long reportId, Long adminUserId, ReportProcessRequestDto requestDto) {
        Report report = getReport(reportId);
        validateNotProcessed(report);

        report.reject(adminUserId, requestDto.processNote());
        reportRepository.save(report);

        sendReportProcessedNotification(report);

        return toProcessResponse(report);
    }

    private void sendReportReceivedNotification(Report report, Long targetAuthorId) {
        if (report.getTargetType() == ReportTargetType.POST) {
            notificationService.createNotification(
                targetAuthorId,
                NotificationType.POST_REPORTED,
                "게시물이 신고됐어요.",
                "회원님의 게시물이 신고 접수되었습니다. 관리자 검토 후 처리될 예정입니다.",
                NotificationReferenceType.POST,
                report.getTargetId());
            return;
        }

        notificationService.createNotification(
            targetAuthorId,
            NotificationType.COMMENT_REPORTED,
            "댓글이 신고됐어요.",
            "회원님의 댓글이 신고 접수되었습니다. 관리자 검토 후 처리될 예정입니다.",
            NotificationReferenceType.COMMENT,
            report.getTargetId());
    }

    private void sendReportProcessedNotification(Report report) {
        boolean blinded = report.getReportStatus() == ReportStatus.BLINDED;

        NotificationType notificationType =
            blinded
                ? NotificationType.REPORT_PROCESSED_BLINDED
                : NotificationType.REPORT_PROCESSED_REJECTED;

        String title = blinded ? "신고가 처리됐어요." : "신고 검토가 완료됐어요.";
        String body =
            blinded
                ? "회원님이 신고한 내용이 검토 후 반영되었습니다."
                : "회원님이 신고한 내용이 검토 완료되었습니다.";

        notificationService.createNotification(
            report.getReporterUserId(),
            notificationType,
            title,
            body,
            resolveReferenceType(report),
            report.getTargetId());
    }

    private NotificationReferenceType resolveReferenceType(Report report) {
        if (report.getTargetType() == ReportTargetType.POST) {
            return NotificationReferenceType.POST;
        }
        return NotificationReferenceType.COMMENT;
    }

    private void blindTarget(Report report) {
        if (report.getTargetType() == ReportTargetType.POST) {
            Post post =
                postRepository
                    .findById(report.getTargetId())
                    .orElseThrow(
                        () ->
                            new CommunityException(
                                CommunityErrorCode.REPORT_TARGET_NOT_FOUND));
            validateBlindable(post);
            post.blind();
            postRepository.save(post);
            return;
        }

        Comment comment =
            commentRepository
                .findById(report.getTargetId())
                .orElseThrow(
                    () ->
                        new CommunityException(
                            CommunityErrorCode.REPORT_TARGET_NOT_FOUND));

        validateBlindable(comment);
        comment.blind();
        commentRepository.save(comment);
    }


    private void validateBlindable(Post post) {
        if (post.getStatus() == PostStatus.DELETED || post.getStatus() == PostStatus.BLINDED) {
            throw new CommunityException(CommunityErrorCode.REPORT_ALREADY_PROCESSED);
        }
    }

    private void validateBlindable(Comment comment) {
        if (comment.getStatus() == CommentStatus.DELETED
            || comment.getStatus() == CommentStatus.BLINDED) {
            throw new CommunityException(CommunityErrorCode.REPORT_ALREADY_PROCESSED);
        }
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
