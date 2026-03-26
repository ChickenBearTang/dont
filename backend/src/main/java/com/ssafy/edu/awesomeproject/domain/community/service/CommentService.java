package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Comment;
import com.ssafy.edu.awesomeproject.domain.community.entity.CommentStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionTargetType;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionType;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.CommentRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.ReactionRepository;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationReferenceType;
import com.ssafy.edu.awesomeproject.domain.notification.entity.NotificationType;
import com.ssafy.edu.awesomeproject.domain.notification.service.NotificationService;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class CommentService {
    private static final List<PostStatus> READABLE_POST_STATUSES =
            List.of(PostStatus.ACTIVE, PostStatus.BLINDED);
    private static final List<CommentStatus> READABLE_COMMENT_STATUSES =
            List.of(CommentStatus.ACTIVE, CommentStatus.BLINDED);
    private static final String BLINDED_COMMENT_MESSAGE = "신고 처리된 댓글입니다.";

    private final CommentRepository commentRepository;
    private final PostRepository postRepository;
    private final UserRepository userRepository;
    private final ReactionRepository reactionRepository;
    private final S3AssetUrlResolver s3AssetUrlResolver;
    private final NotificationService notificationService;

    public CommentService(
            CommentRepository commentRepository,
            PostRepository postRepository,
            UserRepository userRepository,
            ReactionRepository reactionRepository,
            S3AssetUrlResolver s3AssetUrlResolver,
            NotificationService notificationService) {
        this.commentRepository = commentRepository;
        this.postRepository = postRepository;
        this.userRepository = userRepository;
        this.reactionRepository = reactionRepository;
        this.s3AssetUrlResolver = s3AssetUrlResolver;
        this.notificationService = notificationService;
    }

    public CreateCommentResult createComment(
            Long userId, Long postId, Long parentCommentId, String content) {
        Post post =
                postRepository
                        .findByIdAndStatus(postId, PostStatus.ACTIVE)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));

        validateUserCohortAccess(user, post.getBoard());

        Comment parentComment = null;
        if (parentCommentId != null) {
            parentComment =
                    commentRepository
                            .findByIdAndStatus(parentCommentId, CommentStatus.ACTIVE)
                            .orElseThrow(
                                    () -> new CommunityException(CommunityErrorCode.COMMENT_NOT_FOUND));

            if (!parentComment.getPost().getId().equals(postId)) {
                throw new CommunityException(CommunityErrorCode.INVALID_PARENT_COMMENT);
            }
        }

        Comment savedComment = commentRepository.save(new Comment(post, user, parentComment, content));
        sendCommentNotifications(post, parentComment, savedComment, user);

        return new CreateCommentResult(savedComment.getId(), savedComment.getCreatedAt());
    }

    @Transactional(readOnly = true)
    public GetCommentListResult getComments(Long userId, Long postId, Integer page, Integer size) {
        Post post = getReadablePost(userId, postId);

        int pageNumber = normalizePage(page);
        int pageSize = normalizeSize(size, 10);

        List<Comment> allComments =
                commentRepository.findByPost_IdAndStatusInOrderByIdAsc(
                        post.getId(), READABLE_COMMENT_STATUSES);
        Map<Long, Comment> commentById = indexComments(allComments);
        List<Comment> rootComments =
                allComments.stream().filter(comment -> comment.getParentComment() == null).toList();

        int totalElements = rootComments.size();
        int fromIndex = Math.min(pageNumber * pageSize, totalElements);
        int toIndex = Math.min(fromIndex + pageSize, totalElements);
        boolean hasNext = toIndex < totalElements;

        Map<Long, Integer> replyCountByRootId = new HashMap<>();
        for (Comment comment : allComments) {
            if (comment.getParentComment() == null) {
                continue;
            }

            RootResolution resolution = resolveRoot(comment, commentById);
            replyCountByRootId.merge(resolution.rootId(), 1, Integer::sum);
        }

        List<CommentThreadSummary> content =
                rootComments.subList(fromIndex, toIndex).stream()
                        .map(
                                root ->
                                        new CommentThreadSummary(
                                                root.getId(),
                                                null,
                                                root.getStatus().name(),
                                                resolveCommentContent(root),
                                                root.getUser().getId(),
                                                root.getUser().getNickname(),
                                                s3AssetUrlResolver.resolvePublicUrlOrNull(
                                                        root.getUser().getProfileImageUrl()),
                                                root.isAuthor(userId),
                                                countCommentLikes(root.getId()),
                                                root.getCreatedAt(),
                                                root.getUpdatedAt(),
                                                replyCountByRootId.getOrDefault(root.getId(), 0),
                                                List.of()))
                        .toList();

        return new GetCommentListResult(
                content,
                pageNumber,
                pageSize,
                totalElements,
                calculateTotalPages(totalElements, pageSize),
                hasNext);
    }

    @Transactional(readOnly = true)
    public GetCommentReplyListResult getReplies(
            Long userId, Long postId, Long rootCommentId, Integer page, Integer size) {
        Post post = getReadablePost(userId, postId);
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));
        validateUserCohortAccess(user, post.getBoard());

        Comment rootComment =
                commentRepository
                        .findByIdAndStatusIn(rootCommentId, READABLE_COMMENT_STATUSES)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.COMMENT_NOT_FOUND));

        if (!rootComment.getPost().getId().equals(postId) || rootComment.getParentComment() != null) {
            throw new CommunityException(CommunityErrorCode.INVALID_PARENT_COMMENT);
        }

        int pageNumber = normalizePage(page);
        int pageSize = normalizeSize(size, 10);

        List<Comment> allComments =
                commentRepository.findByPost_IdAndStatusInOrderByIdAsc(
                        post.getId(), READABLE_COMMENT_STATUSES);
        Map<Long, Comment> commentById = indexComments(allComments);

        List<CommentReplySummary> replies =
                allComments.stream()
                        .filter(comment -> comment.getParentComment() != null)
                        .map(
                                comment -> {
                                    RootResolution resolution = resolveRoot(comment, commentById);
                                    if (!resolution.rootId().equals(rootCommentId)) {
                                        return null;
                                    }

                                    return new CommentReplySummary(
                                            comment.getId(),
                                            comment.getParentComment() == null
                                                    ? null
                                                    : comment.getParentComment().getId(),
                                            resolution.replyToCommentId(),
                                            resolution.replyToNickname(),
                                            resolution.depth(),
                                            comment.getStatus().name(),
                                            resolveCommentContent(comment),
                                            comment.getUser().getId(),
                                            comment.getUser().getNickname(),
                                            s3AssetUrlResolver.resolvePublicUrlOrNull(
                                                    comment.getUser().getProfileImageUrl()),
                                            comment.isAuthor(userId),
                                            countCommentLikes(comment.getId()),
                                            comment.getCreatedAt(),
                                            comment.getUpdatedAt());
                                })
                        .filter(reply -> reply != null)
                        .toList();

        int totalElements = replies.size();
        int fromIndex = Math.min(pageNumber * pageSize, totalElements);
        int toIndex = Math.min(fromIndex + pageSize, totalElements);
        boolean hasNext = toIndex < totalElements;

        return new GetCommentReplyListResult(
                replies.subList(fromIndex, toIndex),
                pageNumber,
                pageSize,
                totalElements,
                calculateTotalPages(totalElements, pageSize),
                hasNext);
    }

    public UpdateCommentResult updateComment(Long userId, Long commentId, String content) {
        Comment comment =
                commentRepository
                        .findByIdAndStatus(commentId, CommentStatus.ACTIVE)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.COMMENT_NOT_FOUND));

        if (!comment.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.COMMENT_FORBIDDEN);
        }

        comment.update(content);
        return new UpdateCommentResult(comment.getId(), comment.getUpdatedAt());
    }

    public DeleteCommentResult deleteComment(Long userId, Long commentId) {
        Comment comment =
                commentRepository
                        .findByIdAndStatus(commentId, CommentStatus.ACTIVE)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.COMMENT_NOT_FOUND));

        if (!comment.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.COMMENT_FORBIDDEN);
        }

        comment.delete();
        return new DeleteCommentResult(true, comment.getDeletedAt());
    }

    private void sendCommentNotifications(
            Post post, Comment parentComment, Comment savedComment, User commenter) {
        Long commenterUserId = commenter.getId();
        Long postAuthorUserId = post.getUser().getId();

        Set<Long> notifiedUserIds = new HashSet<>();

        if (!postAuthorUserId.equals(commenterUserId)) {
            notificationService.createNotification(
                    postAuthorUserId,
                    NotificationType.POST_COMMENT_CREATED,
                    "내 게시글에 댓글이 달렸어요",
                    commenter.getNickname() + "님이 회원님의 게시글에 댓글을 남겼습니다.",
                    NotificationReferenceType.COMMENT,
                    savedComment.getId());
            notifiedUserIds.add(postAuthorUserId);
        }

        if (parentComment != null) {
            Long parentCommentAuthorUserId = parentComment.getUser().getId();

            if (!parentCommentAuthorUserId.equals(commenterUserId)
                    && !notifiedUserIds.contains(parentCommentAuthorUserId)) {
                notificationService.createNotification(
                        parentCommentAuthorUserId,
                        NotificationType.POST_COMMENT_CREATED,
                        "내 댓글에 답글이 달렸어요",
                        commenter.getNickname() + "님이 회원님의 댓글에 답글을 남겼습니다.",
                        NotificationReferenceType.COMMENT,
                        savedComment.getId());
            }
        }
    }

    private Post getReadablePost(Long userId, Long postId) {
        Post post =
                postRepository
                        .findByIdAndStatusIn(postId, READABLE_POST_STATUSES)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));

        validateUserCohortAccess(user, post.getBoard());
        return post;
    }

    private void validateUserCohortAccess(User user, Board board) {
        if (board.getCategory() != BoardCategory.COHORT) {
            return;
        }

        if (user.getCohort() == null || board.getCohort() == null) {
            throw new CommunityException(CommunityErrorCode.COHORT_FORBIDDEN);
        }

        if (!user.getCohort().getId().equals(board.getCohort().getId())) {
            throw new CommunityException(CommunityErrorCode.COHORT_FORBIDDEN);
        }
    }

    private String resolveCommentContent(Comment comment) {
        if (comment.getStatus() == CommentStatus.BLINDED) {
            return BLINDED_COMMENT_MESSAGE;
        }
        return comment.getContent();
    }

    private Map<Long, Comment> indexComments(List<Comment> comments) {
        Map<Long, Comment> commentById = new HashMap<>();
        for (Comment comment : comments) {
            commentById.put(comment.getId(), comment);
        }
        return commentById;
    }

    private int normalizePage(Integer page) {
        return (page == null || page < 0) ? 0 : page;
    }

    private int normalizeSize(Integer size, int defaultSize) {
        return (size == null || size <= 0) ? defaultSize : size;
    }

    private int calculateTotalPages(int totalElements, int pageSize) {
        return totalElements == 0 ? 0 : (int) Math.ceil((double) totalElements / pageSize);
    }

    private int countCommentLikes(Long commentId) {
        return Math.toIntExact(
                reactionRepository.countByTargetTypeAndTargetIdAndReactionType(
                        ReactionTargetType.COMMENT, commentId, ReactionType.LIKE));
    }

    private RootResolution resolveRoot(Comment comment, Map<Long, Comment> commentById) {
        Comment cursor = comment;
        Comment directParent = comment.getParentComment();
        int depth = 1;

        while (cursor.getParentComment() != null) {
            cursor = commentById.get(cursor.getParentComment().getId());
            if (cursor == null) {
                throw new CommunityException(CommunityErrorCode.INVALID_PARENT_COMMENT);
            }
            if (cursor.getParentComment() != null) {
                depth++;
            }
        }

        return new RootResolution(
                cursor.getId(),
                directParent == null ? null : directParent.getId(),
                directParent == null ? null : directParent.getUser().getNickname(),
                depth);
    }

    public record CreateCommentResult(Long commentId, LocalDateTime createdAt) {}

    public record CommentThreadSummary(
            Long commentId,
            Long parentCommentId,
            String status,
            String content,
            Long authorId,
            String authorNickname,
            String authorProfileImageUrl,
            Boolean isMine,
            Integer likeCount,
            LocalDateTime createdAt,
            LocalDateTime updatedAt,
            Integer replyCount,
            List<CommentReplySummary> replies) {}

    public record CommentReplySummary(
            Long commentId,
            Long parentCommentId,
            Long replyToCommentId,
            String replyToNickname,
            Integer depth,
            String status,
            String content,
            Long authorId,
            String authorNickname,
            String authorProfileImageUrl,
            Boolean isMine,
            Integer likeCount,
            LocalDateTime createdAt,
            LocalDateTime updatedAt) {}

    public record GetCommentListResult(
            List<CommentThreadSummary> content,
            int page,
            int size,
            long totalElements,
            int totalPages,
            boolean hasNext) {}

    public record GetCommentReplyListResult(
            List<CommentReplySummary> content,
            int page,
            int size,
            long totalElements,
            int totalPages,
            boolean hasNext) {}

    public record UpdateCommentResult(Long commentId, LocalDateTime updatedAt) {}

    public record DeleteCommentResult(Boolean deleted, LocalDateTime deletedAt) {}

    private record RootResolution(
            Long rootId, Long replyToCommentId, String replyToNickname, Integer depth) {}
}
