package com.ssafy.edu.awesomeproject.domain.community.service;

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
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class CommentService {
    private final CommentRepository commentRepository;
    private final PostRepository postRepository;
    private final UserRepository userRepository;
    private final ReactionRepository reactionRepository;

    public CommentService(
            CommentRepository commentRepository,
            PostRepository postRepository,
            UserRepository userRepository,
            ReactionRepository reactionRepository) {
        this.commentRepository = commentRepository;
        this.postRepository = postRepository;
        this.userRepository = userRepository;
        this.reactionRepository = reactionRepository;
    }

    public CreateCommentResult createComment(
            Long userId, Long postId, Long parentCommentId, String content) {

        Post post =
                postRepository
                        .findByIdAndStatus(postId, PostStatus.ACTIVE)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));

        validateUserCohortAccess(user, post.getBoard());

        Comment parentComment = null;
        if (parentCommentId != null) {
            parentComment =
                    commentRepository
                            .findByIdAndStatus(parentCommentId, CommentStatus.ACTIVE)
                            .orElseThrow(
                                    () ->
                                            new CommunityException(
                                                    CommunityErrorCode.COMMENT_NOT_FOUND));

            if (!parentComment.getPost().getId().equals(postId)) {
                throw new CommunityException(CommunityErrorCode.INVALID_PARENT_COMMENT);
            }
        }

        Comment comment = new Comment(post, user, parentComment, content);
        Comment savedComment = commentRepository.save(comment);

        return new CreateCommentResult(savedComment.getId(), savedComment.getCreatedAt());
    }

    @Transactional(readOnly = true)
    public GetCommentListResult getComments(Long userId, Long postId, Integer page, Integer size) {
        Post post =
                postRepository
                        .findByIdAndStatus(postId, PostStatus.ACTIVE)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));

        validateUserCohortAccess(user, post.getBoard());

        int pageNumber = (page == null || page < 0) ? 0 : page;
        int pageSize = (size == null || size <= 0) ? 10 : size;

        PageRequest pageRequest =
                PageRequest.of(pageNumber, pageSize, Sort.by(Sort.Direction.ASC, "id"));

        Page<Comment> commentPage =
                commentRepository.findByPost_IdAndStatus(postId, CommentStatus.ACTIVE, pageRequest);

        List<CommentSummary> content =
                commentPage.getContent().stream()
                        .map(
                                comment ->
                                        new CommentSummary(
                                                comment.getId(),
                                                comment.getParentComment() != null
                                                        ? comment.getParentComment().getId()
                                                        : null,
                                                comment.getContent(),
                                                comment.getUser().getId(),
                                                comment.getUser().getNickname(),
                                                comment.isAuthor(userId),
                                                Math.toIntExact(
                                                        reactionRepository
                                                                .countByTargetTypeAndTargetIdAndReactionType(
                                                                        ReactionTargetType.COMMENT,
                                                                        comment.getId(),
                                                                        ReactionType.LIKE)),
                                                comment.getCreatedAt()))
                        .toList();

        return new GetCommentListResult(
                content,
                commentPage.getNumber(),
                commentPage.getSize(),
                commentPage.getTotalElements(),
                commentPage.getTotalPages(),
                commentPage.hasNext());
    }

    public UpdateCommentResult updateComment(Long userId, Long commentId, String content) {
        Comment comment =
                commentRepository
                        .findByIdAndStatus(commentId, CommentStatus.ACTIVE)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.COMMENT_NOT_FOUND));
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
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.COMMENT_NOT_FOUND));
        if (!comment.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.COMMENT_FORBIDDEN);
        }

        comment.delete();

        return new DeleteCommentResult(true, comment.getDeletedAt());
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

    public record CreateCommentResult(Long commentId, LocalDateTime createdAt) {}

    public record CommentSummary(
            Long commentId,
            Long parentCommentId,
            String content,
            Long authorId,
            String authorNickname,
            Boolean isMine,
            Integer likeCount,
            LocalDateTime createdAt) {}

    public record GetCommentListResult(
            List<CommentSummary> content,
            int page,
            int size,
            long totalElements,
            int totalPages,
            boolean hasNext) {}

    public record UpdateCommentResult(Long commentId, LocalDateTime updatedAt) {}

    public record DeleteCommentResult(Boolean deleted, LocalDateTime deletedAt) {}
}
