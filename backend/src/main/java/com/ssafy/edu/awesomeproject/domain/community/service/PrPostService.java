package com.ssafy.edu.awesomeproject.domain.community.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCloseRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PrVoteSubmitRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCloseResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailEventDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailPermissionsDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrDetailReviewDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrVoteSubmitResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrCloseReason;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrCloseTargetStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrEvent;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrEventType;
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
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
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
    private final PostAttachmentService postAttachmentService;
    private final ObjectMapper objectMapper;
    private final S3AssetUrlResolver s3AssetUrlResolver;

    public PrPostService(
            UserRepository userRepository,
            BoardRepository boardRepository,
            PostRepository postRepository,
            PrPostRepository prPostRepository,
            PrVoteRepository prVoteRepository,
            PrReviewRepository prReviewRepository,
            PrEventRepository prEventRepository,

            PostAttachmentService postAttachmentService,

            ObjectMapper objectMapper,
            S3AssetUrlResolver s3AssetUrlResolver) {
        this.userRepository = userRepository;
        this.boardRepository = boardRepository;
        this.postRepository = postRepository;
        this.prPostRepository = prPostRepository;
        this.prVoteRepository = prVoteRepository;
        this.prReviewRepository = prReviewRepository;
        this.prEventRepository = prEventRepository;
        this.postAttachmentService = postAttachmentService;
        this.objectMapper = objectMapper;
        this.s3AssetUrlResolver = s3AssetUrlResolver;
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
        postAttachmentService.syncAttachments(savedPost, prCreateRequestDto.attachments());

        PrPost savedPrPost = prPostRepository.save(toEntity(savedPost, prCreateRequestDto));
        prEventRepository.save(
                new PrEvent(
                        savedPrPost.getPostId(),
                        userId,
                        PrEventType.CREATED,
                        writePayload(
                                Map.of(
                                        "title", prCreateRequestDto.title(),
                                        "itemName", savedPrPost.getItemName(),
                                        "priceAmount", savedPrPost.getPriceAmount()))));

        return new PrCreateResponseDto(
                savedPrPost.getPostId(),
                savedPrPost.getResultStatus(),
                savedPrPost.getDeadlineAt());
    }

    @Transactional
    public PrVoteSubmitResponseDto vote(
            Long postId, Long userId, PrVoteSubmitRequestDto prVoteSubmitRequestDto) {
        PrPost prPost = getPurchaseRequestOrThrow(postId);
        syncDeadlineExpiration(prPost);
        validatePurchaseRequestOpen(prPost);
        validateNotPurchaseRequestOwner(prPost, userId);
        validateNotAlreadyReacted(postId, userId);

        PrVoteValue voteValue = parseVoteValue(prVoteSubmitRequestDto.voteValue());
        PrVote savedVote =
                prVoteRepository.save(
                        new PrVote(
                                postId, userId, voteValue, prVoteSubmitRequestDto.opinionText()));
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
                        writePayload(
                                Map.of(
                                        "decision", mapReviewDecision(voteValue).name(),
                                        "voteValue", voteValue.name(),
                                        "opinionText",
                                                prVoteSubmitRequestDto.opinionText() == null
                                                        ? ""
                                                        : prVoteSubmitRequestDto.opinionText()))));

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
        syncDeadlineExpiration(prPost);
        validatePurchaseRequestOwner(prPost, userId);
        validatePurchaseRequestOpen(prPost);

        PrStatus targetStatus = mapCloseTargetStatus(prCloseRequestDto.resultStatus());
        prPost.close(targetStatus, PrCloseReason.USER_ACTION);
        prEventRepository.save(
                new PrEvent(
                        postId,
                        userId,
                        PrEventType.STATUS_CHANGED,
                        writePayload(
                                Map.of(
                                        "before", PrStatus.OPEN.name(),
                                        "after", targetStatus.name(),
                                        "closeReason", PrCloseReason.USER_ACTION.name()))));

        long agreeCount = prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.AGREE);
        long disagreeCount =
                prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.DISAGREE);
        long totalVoteCount = prVoteRepository.countByPostId(postId);

        return new PrCloseResponseDto(
                prPost.getPostId(),
                prPost.getResultStatusEnum().name(),
                prPost.getResultStatus(),
                agreeCount,
                disagreeCount,
                totalVoteCount,
                prPost.getClosedAt());
    }

    @Transactional
    public PrDetailResponseDto detail(Long postId, Long currentUserId) {
        PrPost prPost = getPurchaseRequestOrThrow(postId);
        syncDeadlineExpiration(prPost);

        long agreeCount = prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.AGREE);
        long disagreeCount =
                prVoteRepository.countByPostIdAndVoteValue(postId, PrVoteValue.DISAGREE);
        long totalVoteCount = prVoteRepository.countByPostId(postId);
        List<PrReview> reviewEntities =
                prReviewRepository.findAllByPostIdOrderByCreatedAtAsc(postId);
        Set<Long> reviewUserIds =
                reviewEntities.stream().map(PrReview::getUserId).collect(Collectors.toSet());
        Map<Long, User> reviewUserById = new HashMap<>();
        if (!reviewUserIds.isEmpty()) {
            userRepository
                    .findAllById(reviewUserIds)
                    .forEach(user -> reviewUserById.put(user.getId(), user));
        }

        List<PrDetailReviewDto> reviews =
                reviewEntities.stream()
                        .map(
                                review -> {
                                    User reviewUser = reviewUserById.get(review.getUserId());
                                    return new PrDetailReviewDto(
                                            review.getId(),
                                            review.getUserId(),
                                            reviewUser == null ? null : reviewUser.getNickname(),
                                            reviewUser == null
                                                    ? null
                                                    : s3AssetUrlResolver.resolvePublicUrlOrNull(
                                                            reviewUser.getProfileImageUrl()),
                                            review.getDecision().name(),
                                            review.getContent(),
                                            review.getCreatedAt());
                                })
                        .toList();
        List<PrDetailEventDto> events = buildEventDtos(postId);

        boolean isOpen = prPost.getResultStatusEnum() == PrStatus.OPEN;
        boolean isAuthor = prPost.getPost().isAuthor(currentUserId);
        boolean alreadyVoted = prVoteRepository.existsByPostIdAndUserId(postId, currentUserId);
        boolean canVote = isOpen && !isAuthor && !alreadyVoted;
        boolean canClose = isOpen && isAuthor;
        Post post = prPost.getPost();

        return new PrDetailResponseDto(
                prPost.getPostId(),
                post.getTitle(),
                post.getUser().getId(),
                post.getUser().getNickname(),
                s3AssetUrlResolver.resolvePublicUrlOrNull(post.getUser().getProfileImageUrl()),
                prPost.getItemName(),
                prPost.getPriceAmount(),
                prPost.getCategory(),
                post.getContent(),
                prPost.getPurchaseUrl(),
                prPost.getDeadlineAt(),
                prPost.getResultStatusEnum().name(),
                prPost.getResultStatus(),
                postAttachmentService.getAttachments(postId),
                post.getCreatedAt(),
                post.getUpdatedAt(),
                agreeCount,
                disagreeCount,
                totalVoteCount,
                prPost.getClosedAt(),
                reviews,
                events,
                new PrDetailPermissionsDto(
                        canVote,
                        canClose,
                        resolveVoteDisabledReason(isOpen, isAuthor, alreadyVoted),
                        resolveCloseDisabledReason(isOpen, isAuthor)));
    }

    private List<PrDetailEventDto> buildEventDtos(Long postId) {
        List<PrEvent> prEvents = prEventRepository.findAllByPostIdOrderByCreatedAtAsc(postId);
        Set<Long> actorIds =
                prEvents.stream()
                        .map(PrEvent::getActorUserId)
                        .filter(id -> id != null)
                        .collect(Collectors.toSet());
        Map<Long, User> actorById = new HashMap<>();
        if (!actorIds.isEmpty()) {
            userRepository.findAllById(actorIds).forEach(user -> actorById.put(user.getId(), user));
        }

        return prEvents.stream()
                .map(
                        event -> {
                            User actor =
                                    event.getActorUserId() == null
                                            ? null
                                            : actorById.get(event.getActorUserId());
                            return new PrDetailEventDto(
                                    event.getId(),
                                    event.getEventType().name(),
                                    event.getActorUserId(),
                                    actor == null ? null : actor.getNickname(),
                                    actor == null
                                            ? null
                                            : s3AssetUrlResolver.resolvePublicUrlOrNull(
                                                    actor.getProfileImageUrl()),
                                    event.getPayload(),
                                    event.getCreatedAt());
                        })
                .toList();
    }

    private String resolveVoteDisabledReason(
            boolean isOpen, boolean isAuthor, boolean alreadyVoted) {
        if (!isOpen) return "종료된 PR은 투표할 수 없습니다.";
        if (isAuthor) return "작성자는 자신의 PR에 투표할 수 없습니다.";
        if (alreadyVoted) return "이미 투표한 PR입니다.";
        return null;
    }

    private String resolveCloseDisabledReason(boolean isOpen, boolean isAuthor) {
        if (!isOpen) return "이미 종료된 PR입니다.";
        if (!isAuthor) return "작성자만 PR을 종료할 수 있습니다.";
        return null;
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
                .orElseThrow(
                        () ->
                                new CommunityException(
                                        CommunityErrorCode.PURCHASE_REQUEST_NOT_FOUND));
    }

    private void validatePurchaseRequestOwner(PrPost prPost, Long userId) {
        if (!prPost.getPost().isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_FORBIDDEN);
        }
    }

    private void validateNotPurchaseRequestOwner(PrPost prPost, Long userId) {
        if (prPost.getPost().isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_FORBIDDEN);
        }
    }

    private void validatePurchaseRequestOpen(PrPost prPost) {
        if (prPost.getResultStatusEnum() != PrStatus.OPEN) {
            throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_NOT_OPEN);
        }
    }

    private void syncDeadlineExpiration(PrPost prPost) {
        if (prPost.getResultStatusEnum() != PrStatus.OPEN
                || !isDeadlineExpired(prPost.getDeadlineAt())) {
            return;
        }

        prPost.close(PrStatus.CLOSED, PrCloseReason.DEADLINE_EXPIRED);
        prEventRepository.save(
                new PrEvent(
                        prPost.getPostId(),
                        null,
                        PrEventType.STATUS_CHANGED,
                        writePayload(
                                Map.of(
                                        "before", PrStatus.OPEN.name(),
                                        "after", PrStatus.CLOSED.name(),
                                        "closeReason", PrCloseReason.DEADLINE_EXPIRED.name()))));
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

    private JsonNode writePayload(Map<String, Object> payload) {
        return objectMapper.valueToTree(payload);
    }

    private PrPost toEntity(Post post, PrCreateRequestDto prCreateRequestDto) {
        return new PrPost(
                post,
                prCreateRequestDto.itemName(),
                prCreateRequestDto.priceAmount(),
                prCreateRequestDto.category(),
                prCreateRequestDto.purchaseUrl(),
                prCreateRequestDto.deadlineAt());
    }
}
