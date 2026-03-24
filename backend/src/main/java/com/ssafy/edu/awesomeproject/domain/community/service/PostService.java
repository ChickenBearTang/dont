package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PostAttachmentRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PostAttachmentResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.CommentStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.HotdealPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.PollPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionTargetType;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionType;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.CommentRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.HotdealPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PollPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PollVoteRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrVoteRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.ReactionRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class PostService {
    private static final List<PostStatus> READABLE_POST_STATUSES =
            List.of(PostStatus.ACTIVE, PostStatus.BLINDED);
    private static final List<CommentStatus> READABLE_COMMENT_STATUSES =
            List.of(CommentStatus.ACTIVE, CommentStatus.BLINDED);
    private static final String BLINDED_POST_MESSAGE = "신고 처리된 게시물입니다.";

    private final PostRepository postRepository;
    private final BoardRepository boardRepository;
    private final UserRepository userRepository;
    private final CohortRepository cohortRepository;
    private final PrPostRepository prPostRepository;
    private final PrVoteRepository prVoteRepository;
    private final HotdealPostRepository hotdealPostRepository;
    private final PollPostRepository pollPostRepository;
    private final PollVoteRepository pollVoteRepository;
    private final ReactionRepository reactionRepository;
    private final CommentRepository commentRepository;
    private final PostAttachmentService postAttachmentService;
    private final S3AssetUrlResolver s3AssetUrlResolver;

    public PostService(
            PostRepository postRepository,
            BoardRepository boardRepository,
            CohortRepository cohortRepository,
            UserRepository userRepository,
            PrPostRepository prPostRepository,
            PrVoteRepository prVoteRepository,
            HotdealPostRepository hotdealPostRepository,
            PollPostRepository pollPostRepository,
            PollVoteRepository pollVoteRepository,
            ReactionRepository reactionRepository,
            CommentRepository commentRepository,
            PostAttachmentService postAttachmentService,
            S3AssetUrlResolver s3AssetUrlResolver) {
        this.postRepository = postRepository;
        this.boardRepository = boardRepository;
        this.cohortRepository = cohortRepository;
        this.userRepository = userRepository;
        this.prPostRepository = prPostRepository;
        this.prVoteRepository = prVoteRepository;
        this.hotdealPostRepository = hotdealPostRepository;
        this.pollPostRepository = pollPostRepository;
        this.pollVoteRepository = pollVoteRepository;
        this.reactionRepository = reactionRepository;
        this.commentRepository = commentRepository;
        this.postAttachmentService = postAttachmentService;
        this.s3AssetUrlResolver = s3AssetUrlResolver;
    }

    public CreatePostResult createPost(
            Long userId,
            BoardCategory category,
            Integer generationNo,
            String title,
            String content,
            List<PostAttachmentRequestDto> attachments) {

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AuthException(CommunityErrorCode.USER_NOT_FOUND));

        Integer resolvedGenerationNo = generationNo;

        if (category == BoardCategory.COHORT) {
            resolvedGenerationNo = getUserGenerationNo(user);

            if (resolvedGenerationNo == null || resolvedGenerationNo < 0) {
                throw new CommunityException(CommunityErrorCode.COHORT_FORBIDDEN);
            }
        }

        validateCategoryAndCohort(category, resolvedGenerationNo);
        Board board = resolveBoard(category, resolvedGenerationNo);

        if (category == BoardCategory.COHORT) {
            validateUserCohort(user, resolvedGenerationNo);
        }

        Post post = new Post(board, user, title, content);
        Post savedPost = postRepository.save(post);
        postAttachmentService.syncAttachments(savedPost, attachments);

        return new CreatePostResult(
                savedPost.getId(),
                savedPost.getBoard().getCategory().name(),
                extractGenerationNo(savedPost.getBoard()),
                savedPost.getCreatedAt());
    }

    @Transactional(readOnly = true)
    public GetPostResult getPost(Long userId, Long postId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AuthException(CommunityErrorCode.USER_NOT_FOUND));

        Post post =
                postRepository
                        .findByIdAndStatusIn(postId, READABLE_POST_STATUSES)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        validatePostReadAccess(user, post);

        return new GetPostResult(
                post.getId(),
                post.getBoard().getCategory().name(),
                extractGenerationNo(post.getBoard()),
                post.getStatus().name(),
                resolvePostTitle(post),
                resolvePostContent(post),
                post.getUser().getId(),
                post.getUser().getNickname(),
                s3AssetUrlResolver.resolvePublicUrlOrNull(post.getUser().getProfileImageUrl()),
                post.isAuthor(userId),
                Math.toIntExact(
                        reactionRepository.countByTargetTypeAndTargetIdAndReactionType(
                                ReactionTargetType.POST, post.getId(), ReactionType.LIKE)),
                Math.toIntExact(
                        reactionRepository.countByTargetTypeAndTargetIdAndReactionType(
                                ReactionTargetType.POST, post.getId(), ReactionType.DISLIKE)),
                Math.toIntExact(
                        commentRepository.countByPost_IdAndStatusIn(
                                post.getId(), READABLE_COMMENT_STATUSES)),

                postAttachmentService.getAttachments(post.getId()),

                post.getCreatedAt(),
                post.getUpdatedAt());
    }

    @Transactional(readOnly = true)
    public GetPostListResult getPostsByCategory(
            Long userId, BoardCategory category, Integer generationNo, Integer page, Integer size) {

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AuthException(CommunityErrorCode.USER_NOT_FOUND));

        int pageNumber = (page == null || page < 0) ? 0 : page;
        int pageSize = (size == null || size <= 0) ? 5 : size;

        Integer resolvedGenerationNo = generationNo;

        if (category != null && category != BoardCategory.COHORT) {
            validateCategoryAndCohort(category, generationNo);
        }

        if (category == BoardCategory.COHORT && resolvedGenerationNo == null) {
            resolvedGenerationNo = getUserGenerationNo(user);
        }

        PageRequest pageRequest =
                PageRequest.of(pageNumber, pageSize, Sort.by(Sort.Direction.DESC, "id"));

        Page<Post> postPage;
        if (category == null) {
            Integer userGenerationNo = getUserGenerationNo(user);

            postPage =
                    postRepository.findVisiblePostsForUser(
                            READABLE_POST_STATUSES,
                            BoardCategory.COHORT,
                            userGenerationNo,
                            pageRequest);
        } else if (category == BoardCategory.COHORT) {
            validateUserCohort(user, resolvedGenerationNo);

            postPage =
                    postRepository.findByBoard_CategoryAndBoard_Cohort_GenerationNoAndStatusIn(
                            category, resolvedGenerationNo, READABLE_POST_STATUSES, pageRequest);
        } else {
            postPage =
                    postRepository.findByBoard_CategoryAndStatusIn(
                            category, READABLE_POST_STATUSES, pageRequest);
        }

        Map<Long, PrPost> prByPostId = getPrByPostId(postPage.getContent(), category);
        Map<Long, PrVoteSummary> voteSummaryByPostId =
                getPrVoteSummaryByPostId(postPage.getContent(), category);
        Map<Long, HotdealPost> hotdealByPostId =
                getHotdealByPostId(postPage.getContent(), category);
        Map<Long, PollPost> pollByPostId = getPollByPostId(postPage.getContent(), category);
        Map<Long, PollVoteSummary> pollVoteSummaryByPostId =
                getPollVoteSummaryByPostId(postPage.getContent(), category);
        Set<Long> postIds = postPage.getContent().stream().map(Post::getId).collect(Collectors.toSet());
        Map<Long, Integer> attachmentCountByPostId =
                postAttachmentService.getAttachmentCountByPostIds(postIds);

        List<PostSummary> content =
                postPage.getContent().stream()
                        .map(
                                post -> {
                                    PostExtraSummary extraSummary = null;

                                    if (post.getStatus() != PostStatus.BLINDED) {
                                        PrSummary prSummary =
                                                buildPrSummary(
                                                        prByPostId,
                                                        voteSummaryByPostId,
                                                        post.getId());
                                        HotdealSummary hotdealSummary =
                                                buildHotdealSummary(hotdealByPostId, post.getId());
                                        PollSummary pollSummary =
                                                buildPollSummary(
                                                        pollByPostId,
                                                        pollVoteSummaryByPostId,
                                                        post.getId());

                                        if (prSummary != null
                                                || hotdealSummary != null
                                                || pollSummary != null) {
                                            extraSummary =
                                                    new PostExtraSummary(
                                                            prSummary, hotdealSummary, pollSummary);
                                        }
                                    }

                                    return new PostSummary(
                                            post.getId(),
                                            post.getBoard().getCategory().name(),
                                            extractGenerationNo(post.getBoard()),
                                            post.getStatus().name(),
                                            resolvePostTitle(post),
                                            post.getUser().getId(),
                                            post.getUser().getNickname(),
                                            s3AssetUrlResolver.resolvePublicUrlOrNull(
                                                    post.getUser().getProfileImageUrl()),
                                            post.isAuthor(userId),
                                            Math.toIntExact(
                                                    reactionRepository
                                                            .countByTargetTypeAndTargetIdAndReactionType(
                                                                    ReactionTargetType.POST,
                                                                    post.getId(),
                                                                    ReactionType.LIKE)),
                                            attachmentCountByPostId.getOrDefault(post.getId(), 0),
                                            Math.toIntExact(
                                                    commentRepository.countByPost_IdAndStatusIn(
                                                            post.getId(),
                                                            READABLE_COMMENT_STATUSES)),
                                            post.getCreatedAt(),
                                            extraSummary);
                                })
                        .toList();

        return new GetPostListResult(
                content,
                postPage.getNumber(),
                postPage.getSize(),
                postPage.getTotalElements(),
                postPage.getTotalPages(),
                postPage.hasNext());
    }

    public UpdatePostResult updatePost(
            Long userId,
            Long postId,
            String title,
            String content,
            List<PostAttachmentRequestDto> attachments) {
        Post post =
                postRepository
                        .findByIdAndStatus(postId, PostStatus.ACTIVE)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        if (!post.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.POST_FORBIDDEN);
        }

        post.update(title, content);
        postAttachmentService.syncAttachments(post, attachments);
        return new UpdatePostResult(post.getId(), post.getUpdatedAt());
    }

    public DeletePostResult deletePost(Long userId, Long postId) {
        Post post =
                postRepository
                        .findByIdAndStatus(postId, PostStatus.ACTIVE)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        if (!post.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.POST_FORBIDDEN);
        }

        post.delete();
        return new DeletePostResult(true, post.getDeletedAt());
    }

    private void validatePostReadAccess(User user, Post post) {
        if (post.getBoard().getCategory() == BoardCategory.COHORT) {
            Integer postGenerationNo = extractGenerationNo(post.getBoard());
            validateUserCohort(user, postGenerationNo);
        }
    }

    private Integer getUserGenerationNo(User user) {
        if (user.getCohort() == null) {
            return -1;
        }
        return user.getCohort().getGenerationNo();
    }

    private Board resolveBoard(BoardCategory category, Integer generationNo) {
        if (category == BoardCategory.COHORT) {
            cohortRepository
                    .findByGenerationNo(generationNo)
                    .orElseThrow(() -> new CommunityException(CommunityErrorCode.COHORT_NOT_FOUND));

            return boardRepository
                    .findByCategoryAndCohort_GenerationNo(category, generationNo)
                    .orElseThrow(() -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));
        }

        return boardRepository
                .findByCategory(category)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));
    }

    private void validateCategoryAndCohort(BoardCategory category, Integer generationNo) {
        if (category == BoardCategory.COHORT && generationNo == null) {
            throw new CommunityException(CommunityErrorCode.COHORT_ID_REQUIRED);
        }

        if (category != BoardCategory.COHORT && generationNo != null) {
            throw new CommunityException(CommunityErrorCode.INVALID_CATEGORY_AND_COHORT);
        }
    }

    private void validateUserCohort(User user, Integer generationNo) {
        if (user.getCohort() == null) {
            throw new CommunityException(CommunityErrorCode.COHORT_FORBIDDEN);
        }

        if (!user.getCohort().getGenerationNo().equals(generationNo)) {
            throw new CommunityException(CommunityErrorCode.COHORT_FORBIDDEN);
        }
    }

    private Integer extractGenerationNo(Board board) {
        return board.getCohort() != null ? board.getCohort().getGenerationNo() : null;
    }

    private String resolvePostTitle(Post post) {
        if (post.getStatus() == PostStatus.BLINDED) {
            return BLINDED_POST_MESSAGE;
        }
        return post.getTitle();
    }

    private String resolvePostContent(Post post) {
        if (post.getStatus() == PostStatus.BLINDED) {
            return BLINDED_POST_MESSAGE;
        }
        return post.getContent();
    }

    private Map<Long, PrPost> getPrByPostId(List<Post> posts, BoardCategory category) {
        if (posts.isEmpty() || category != BoardCategory.PR) {
            return Map.of();
        }

        Set<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toSet());
        return prPostRepository.findByPostIdIn(postIds).stream()
                .collect(Collectors.toMap(PrPost::getPostId, Function.identity()));
    }

    private Map<Long, PrVoteSummary> getPrVoteSummaryByPostId(
            List<Post> posts, BoardCategory category) {
        if (posts.isEmpty() || category != BoardCategory.PR) {
            return Map.of();
        }

        Set<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toSet());
        return prVoteRepository.aggregateByPostIds(postIds).stream()
                .collect(
                        Collectors.toMap(
                                PrVoteRepository.PrVoteCountProjection::getPostId,
                                projection -> new PrVoteSummary(projection.getTotalVoteCount())));
    }

    private PrSummary buildPrSummary(
            Map<Long, PrPost> prByPostId,
            Map<Long, PrVoteSummary> voteSummaryByPostId,
            Long postId) {
        PrPost prPost = prByPostId.get(postId);
        if (prPost == null) {
            return null;
        }

        PrVoteSummary summary = voteSummaryByPostId.get(postId);
        Long totalVoteCount = summary != null ? summary.totalVoteCount() : null;

        return new PrSummary(
                prPost.getResultStatusEnum() == PrStatus.OPEN
                        ? PrStatus.OPEN.name()
                        : PrStatus.CLOSED.name(),
                prPost.getResultStatus(),
                prPost.getItemName(),
                prPost.getPriceAmount(),
                totalVoteCount,
                prPost.getDeadlineAt());
    }

    private Map<Long, HotdealPost> getHotdealByPostId(List<Post> posts, BoardCategory category) {
        if (posts.isEmpty() || category != BoardCategory.HOTDEAL) {
            return Map.of();
        }

        Set<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toSet());
        return hotdealPostRepository.findByPostIdIn(postIds).stream()
                .collect(Collectors.toMap(HotdealPost::getPostId, Function.identity()));
    }

    private HotdealSummary buildHotdealSummary(
            Map<Long, HotdealPost> hotdealByPostId, Long postId) {
        HotdealPost hotdealPost = hotdealByPostId.get(postId);
        if (hotdealPost == null) {
            return null;
        }

        LocalDateTime expiredAt = hotdealPost.getExpiredAt();
        Boolean isExpired = expiredAt != null ? !expiredAt.isAfter(LocalDateTime.now()) : null;

        return new HotdealSummary(
                hotdealPost.getDealPriceAmount(),
                hotdealPost.getOriginalPriceAmount(),
                hotdealPost.getStoreName(),
                expiredAt,
                isExpired);
    }

    private Map<Long, PollPost> getPollByPostId(List<Post> posts, BoardCategory category) {
        if (posts.isEmpty() || category != BoardCategory.POLL) {
            return Map.of();
        }

        Set<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toSet());
        return pollPostRepository.findByPostIdIn(postIds).stream()
                .collect(Collectors.toMap(PollPost::getPostId, Function.identity()));
    }

    private Map<Long, PollVoteSummary> getPollVoteSummaryByPostId(
            List<Post> posts, BoardCategory category) {
        if (posts.isEmpty() || category != BoardCategory.POLL) {
            return Map.of();
        }

        Set<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toSet());
        return pollVoteRepository.aggregateByPostIds(postIds).stream()
                .collect(
                        Collectors.toMap(
                                PollVoteRepository.PollVoteCountProjection::getPostId,
                                projection ->
                                        new PollVoteSummary(
                                                projection.getOptionACount(),
                                                projection.getOptionBCount(),
                                                projection.getTotalVoteCount())));
    }

    private PollSummary buildPollSummary(
            Map<Long, PollPost> pollByPostId,
            Map<Long, PollVoteSummary> pollVoteSummaryByPostId,
            Long postId) {
        PollPost pollPost = pollByPostId.get(postId);
        if (pollPost == null) {
            return null;
        }

        PollVoteSummary voteSummary =
                pollVoteSummaryByPostId.getOrDefault(postId, new PollVoteSummary(0L, 0L, 0L));

        return new PollSummary(
                pollPost.getQuestion(),
                pollPost.getOptionA(),
                pollPost.getOptionB(),
                pollPost.getDeadlineAt(),
                pollPost.isClosed(LocalDateTime.now()),
                voteSummary.optionACount(),
                voteSummary.optionBCount(),
                voteSummary.totalVoteCount());
    }

    public record CreatePostResult(
            Long postId, String category, Integer generationNo, LocalDateTime createdAt) {}

    public record GetPostResult(
            Long postId,
            String category,
            Integer generationNo,
            String status,
            String title,
            String content,
            Long authorId,
            String authorNickname,
            String authorProfileImageUrl,
            Boolean isMine,
            Integer likeCount,
            Integer dislikeCount,
            Integer commentCount,
            List<PostAttachmentResponseDto> attachments,
            LocalDateTime createdAt,
            LocalDateTime updatedAt) {}

    public record PostSummary(
            Long postId,
            String category,
            Integer generationNo,
            String status,
            String title,
            Long authorId,
            String authorNickname,
            String authorProfileImageUrl,
            Boolean isMine,
            Integer likeCount,
            Integer attachmentCount,
            Integer commentCount,
            LocalDateTime createdAt,
            PostExtraSummary extraSummary) {}

    private record PrVoteSummary(Long totalVoteCount) {}

    private record PollVoteSummary(Long optionACount, Long optionBCount, Long totalVoteCount) {}

    public record PostExtraSummary(PrSummary pr, HotdealSummary hotdeal, PollSummary poll) {}

    public record PrSummary(
            String status,
            String resultStatus,
            String itemName,
            Long priceAmount,
            Long totalVoteCount,
            LocalDateTime deadlineAt) {}

    public record HotdealSummary(
            Long dealPriceAmount,
            Long originalPriceAmount,
            String storeName,
            LocalDateTime expiredAt,
            Boolean isExpired) {}

    public record PollSummary(
            String question,
            String optionA,
            String optionB,
            LocalDateTime deadlineAt,
            Boolean isClosed,
            Long optionACount,
            Long optionBCount,
            Long totalVoteCount) {}

    public record GetPostListResult(
            List<PostSummary> content,
            int page,
            int size,
            long totalElements,
            int totalPages,
            boolean hasNext) {}

    public record UpdatePostResult(Long postId, LocalDateTime updatedAt) {}

    public record DeletePostResult(Boolean deleted, LocalDateTime deletedAt) {}
}
