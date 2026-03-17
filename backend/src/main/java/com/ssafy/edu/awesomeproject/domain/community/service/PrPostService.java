package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCloseRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrVoteSubmitRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCloseResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailEventDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailPermissionsDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailReviewDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrVoteSubmitResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrEvent;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrEventType;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrCloseReason;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrCloseTargetStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrReview;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrReviewDecision;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrVote;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrVoteValue;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrEventRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrReviewRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrVoteRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class PrPostService {
    private final UserRepository userRepository;
    private final BoardRepository boardRepository;
    private final PostRepository postRepository;
    private final PrPostRepository prPostRepository;
    private final PrVoteRepository prVoteRepository;
    private final PrReviewRepository prReviewRepository;
    private final PrEventRepository prEventRepository;

    public PrPostService(
            UserRepository userRepository,
            BoardRepository boardRepository,
            PostRepository postRepository,
            PrPostRepository prPostRepository,
            PrVoteRepository prVoteRepository,
            PrReviewRepository prReviewRepository,
            PrEventRepository prEventRepository) {
        this.userRepository = userRepository;
        this.boardRepository = boardRepository;
        this.postRepository = postRepository;
        this.prPostRepository = prPostRepository;
        this.prVoteRepository = prVoteRepository;
        this.prReviewRepository = prReviewRepository;
        this.prEventRepository = prEventRepository;
    }

    @Transactional
    public PrCreateResponseDto create(Long userId, PrCreateRequestDto prCreateRequestDto) {
        User user = getUserOrThrow(userId);
        Board prBoard = getPrBoardOrThrow();

        Post savedPost =
                postRepository.save(
                        new Post(
                                prBoard,
                                user,
                                prCreateRequestDto.title(),
                                prCreateRequestDto.content()));

        PrPost savedPrPost = prPostRepository.save(toEntity(savedPost, prCreateRequestDto));
        prEventRepository.save(
                new PrEvent(
                        savedPrPost.getPostId(),
                        userId,
                        PrEventType.CREATED,
                        "PR created: " + savedPrPost.getItemName()));

        return new PrCreateResponseDto(
                savedPrPost.getPostId(),
                savedPrPost.getResultStatus(),
                savedPrPost.getDeadlineAt());
    }

    @Transactional
    public PrVoteSubmitResponseDto vote(
            Long postId, Long userId, PrVoteSubmitRequestDto prVoteSubmitRequestDto) {
        PrPost prPost = getPurchaseRequestOrThrow(postId);
        validatePurchaseRequestOpen(prPost, true);
        validateNotAlreadyReacted(postId, userId);

        PrVoteValue voteValue = parseVoteValue(prVoteSubmitRequestDto.voteValue());
        PrVote savedVote =
                prVoteRepository.save(
                        new PrVote(
                                postId,
                                userId,
                                voteValue,
                                prVoteSubmitRequestDto.opinionText()));
        prReviewRepository.save(
                new PrReview(
                        postId,
                        userId,
                        mapReviewDecision(voteValue),
                        prVoteSubmitRequestDto.opinionText()));
        prEventRepository.save(
                new PrEvent(
                        postId,
                        userId,
                        PrEventType.REVIEW_SUBMITTED,
                        "Review submitted: " + voteValue.name()));

        return new PrVoteSubmitResponseDto(
                savedVote.getPostId(),
                savedVote.getUserId(),
                savedVote.getVoteValue().name(),
                savedVote.getOpinionText(),
                savedVote.getCreatedAt());
    }

    @Transactional
    public PrCloseResponseDto close(Long postId, Long userId, PrCloseRequestDto prCloseRequestDto) {
        PrPost prPost = getPurchaseRequestOrThrow(postId);
        validatePurchaseRequestOwner(prPost, userId);
        validatePurchaseRequestOpen(prPost, true);

        PrStatus targetStatus = mapCloseTargetStatus(prCloseRequestDto.resultStatus());
        prPost.close(targetStatus, PrCloseReason.USER_ACTION);
        prEventRepository.save(
                new PrEvent(
                        postId,
                        userId,
                        PrEventType.STATUS_CHANGED,
                        "Status changed to " + targetStatus.name()));

        long agreeCount = prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.AGREE);
        long disagreeCount = prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.DISAGREE);
        long totalVoteCount = prVoteRepository.countByPostId(postId);

        return new PrCloseResponseDto(
                prPost.getPostId(),
                PrStatus.CLOSED.name(),
                prPost.getResultStatus(),
                agreeCount,
                disagreeCount,
                totalVoteCount,
                prPost.getClosedAt());
    }

    public PrDetailResponseDto detail(Long postId) {
        PrPost prPost = getPurchaseRequestOrThrow(postId);

        long agreeCount = prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.AGREE);
        long disagreeCount = prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.DISAGREE);
        long totalVoteCount = prVoteRepository.countByPostId(postId);
        List<PrDetailReviewDto> reviews =
                prReviewRepository.findAllByPostIdOrderByCreatedAtAsc(postId).stream()
                        .map(
                                review ->
                                        new PrDetailReviewDto(
                                                review.getId(),
                                                review.getUserId(),
                                                review.getDecision().name(),
                                                review.getContent(),
                                                review.getCreatedAt()))
                        .toList();
        List<PrDetailEventDto> events =
                prEventRepository.findAllByPostIdOrderByCreatedAtAsc(postId).stream()
                        .map(
                                event ->
                                        new PrDetailEventDto(
                                                event.getId(),
                                                event.getEventType().name(),
                                                event.getActorUserId(),
                                                event.getPayload(),
                                                event.getCreatedAt()))
                        .toList();

        String status =
                prPost.getResultStatusEnum() == PrStatus.OPEN
                        ? PrStatus.OPEN.name()
                        : PrStatus.CLOSED.name();

        return new PrDetailResponseDto(
                prPost.getPostId(),
                prPost.getItemName(),
                prPost.getPriceAmount(),
                prPost.getCategory(),
                prPost.getPost().getContent(),
                prPost.getPurchaseUrl(),
                prPost.getImageUrl(),
                status,
                prPost.getResultStatus(),
                agreeCount,
                disagreeCount,
                totalVoteCount,
                prPost.getClosedAt(),
                reviews,
                events,
                new PrDetailPermissionsDto(
                        prPost.getResultStatusEnum() == PrStatus.OPEN,
                        prPost.getResultStatusEnum() == PrStatus.OPEN));
    }

    private User getUserOrThrow(Long userId) {
        return userRepository
                .findById(userId)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));
    }

    private Board getPrBoardOrThrow() {
        return boardRepository
                .findByCategory(BoardCategory.PR)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));
    }

    private PrPost getPurchaseRequestOrThrow(Long postId) {
        return prPostRepository
                .findByPost_Id(postId)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_NOT_FOUND));
    }

    private void validatePurchaseRequestOwner(PrPost prPost, Long userId) {
        if (!prPost.getPost().isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_FORBIDDEN);
        }
    }

    private void validatePurchaseRequestOpen(PrPost prPost, boolean autoCloseOnDeadlineExpired) {
        if (autoCloseOnDeadlineExpired
                && prPost.getResultStatusEnum() == PrStatus.OPEN
                && isDeadlineExpired(prPost.getDeadlineAt())) {
            prPost.close(PrStatus.CLOSED, PrCloseReason.DEADLINE_EXPIRED);
        }

        if (prPost.getResultStatusEnum() != PrStatus.OPEN) {
            throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_NOT_OPEN);
        }
    }

    private boolean isDeadlineExpired(LocalDateTime deadlineAt) {
        if (deadlineAt == null) {
            return false;
        }

        return !deadlineAt.isAfter(LocalDateTime.now());
    }

    private void validateNotAlreadyReacted(Long postId, Long userId) {
        if (prVoteRepository.existsByPostIdAndUserId(postId, userId)) {
            throw new CommunityException(CommunityErrorCode.ALREADY_REACTED);
        }
    }

    private PrVoteValue parseVoteValue(String voteValue) {
        try {
            return PrVoteValue.valueOf(voteValue.trim().toUpperCase(Locale.ROOT));
        } catch (RuntimeException exception) {
            throw new CommunityException(CommunityErrorCode.INVALID_INPUT);
        }
    }

    private PrStatus mapCloseTargetStatus(PrCloseTargetStatus closeTargetStatus) {
        if (closeTargetStatus == PrCloseTargetStatus.MERGED) {
            return PrStatus.MERGED;
        }

        return PrStatus.CLOSED;
    }

    private PrReviewDecision mapReviewDecision(PrVoteValue voteValue) {
        if (voteValue == PrVoteValue.AGREE) {
            return PrReviewDecision.APPROVE;
        }
        return PrReviewDecision.REQUEST_CHANGES;
    }

    private PrPost toEntity(Post post, PrCreateRequestDto prCreateRequestDto) {
        return new PrPost(
                post,
                prCreateRequestDto.itemName(),
                prCreateRequestDto.priceAmount(),
                prCreateRequestDto.category(),
                prCreateRequestDto.purchaseUrl(),
                prCreateRequestDto.imageUrl(),
                prCreateRequestDto.deadlineAt());
    }
}
