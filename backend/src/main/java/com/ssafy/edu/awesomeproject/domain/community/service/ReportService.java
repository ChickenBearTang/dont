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

        return new ReportCreateResponseDto(report.getId(), report.getReportStatus().name(), report.getCreatedAt());
    }

    private void validateOtherReasonDetail(ReportReasonCode reasonCode, String detailText) {
        if (reasonCode == ReportReasonCode.OTHER && (detailText == null || detailText.isBlank())) {
            throw new CommunityException(CommunityErrorCode.INVALID_INPUT);
        }
    }

    private void validateDuplicateReport(Long reporterUserId, ReportTargetType targetType, Long targetId) {
        if (reportRepository.existsByReporterUserIdAndTargetTypeAndTargetId(reporterUserId, targetType, targetId)) {
            throw new CommunityException(CommunityErrorCode.REPORT_ALREADY_EXISTS);
        }
    }

    private Long resolveTargetAuthorId(ReportTargetType targetType, Long targetId) {
        if (targetType == ReportTargetType.POST) {
            Post post =
                    postRepository
                            .findByIdAndStatus(targetId, PostStatus.ACTIVE)
                            .orElseThrow(() -> new CommunityException(CommunityErrorCode.REPORT_TARGET_NOT_FOUND));
            return post.getUser().getId();
        }

        Comment comment =
                commentRepository
                        .findByIdAndStatus(targetId, CommentStatus.ACTIVE)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.REPORT_TARGET_NOT_FOUND));
        return comment.getUser().getId();
    }
}

