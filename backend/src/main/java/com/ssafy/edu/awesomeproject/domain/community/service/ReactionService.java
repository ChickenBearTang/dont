package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Comment;
import com.ssafy.edu.awesomeproject.domain.community.entity.CommentStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.Reaction;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionTargetType;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionType;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.CommentRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.ReactionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class ReactionService {
    private final ReactionRepository reactionRepository;
    private final PostRepository postRepository;
    private final CommentRepository commentRepository;
    private final UserRepository userRepository;

    public ReactionService(
            ReactionRepository reactionRepository,
            PostRepository postRepository,
            CommentRepository commentRepository,
            UserRepository userRepository) {
        this.reactionRepository = reactionRepository;
        this.postRepository = postRepository;
        this.commentRepository = commentRepository;
        this.userRepository = userRepository;
    }

    public ToggleReactionResult toggleReaction(
            Long userId,
            ReactionTargetType targetType,
            Long targetId,
            ReactionType reactionType,
            Boolean active) {

        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(() -> new AuthException(CommunityErrorCode.USER_NOT_FOUND));

        validateTargetAccess(user, targetType, targetId);

        // 반응 등록 or 취소
        // ACTIVE = true (등록)
        // ACTIVE = false (취소)
        if (Boolean.TRUE.equals(active)) {
            registerReaction(user, targetType, targetId, reactionType);
        } else {
            cancelReaction(userId, targetType, targetId, reactionType);
        }

        return new ToggleReactionResult(
                targetType.name(),
                targetId,
                reactionType.name(),
                active,
                Math.toIntExact(countReaction(targetType, targetId, reactionType.LIKE)),
                Math.toIntExact(countReaction(targetType, targetId, reactionType.DISLIKE)));
    }

    @Transactional(readOnly = true)
    public long countReaction(
            ReactionTargetType targetType, Long targetId, ReactionType reactionType) {
        return reactionRepository.countByTargetTypeAndTargetIdAndReactionType(
                targetType, targetId, reactionType);
    }

    private void registerReaction(
            User user, ReactionTargetType targetType, Long targetId, ReactionType reactionType) {

        // 중복 방지 (ifPresent)
        reactionRepository
                .findByUser_IdAndTargetTypeAndTargetIdAndReactionType(
                        user.getId(), targetType, targetId, reactionType)
                .ifPresent(
                        reaction -> {
                            throw new CommunityException(CommunityErrorCode.ALREADY_REACTED);
                        });

        Reaction reaction = new Reaction(user, targetType, targetId, reactionType);
        reactionRepository.save(reaction);
    }

    private void cancelReaction(
            Long userId, ReactionTargetType targetType, Long targetId, ReactionType reactionType) {

        reactionRepository
                .findByUser_IdAndTargetTypeAndTargetIdAndReactionType(
                        userId, targetType, targetId, reactionType)
                .ifPresent(reactionRepository::delete);
    }

    private void validateTargetAccess(User user, ReactionTargetType targetType, Long targetId) {
        // POST에 반응 등록
        if (targetType == ReactionTargetType.POST) {
            Post post =
                    postRepository
                            .findByIdAndStatus(targetId, PostStatus.ACTIVE)
                            .orElseThrow(
                                    () ->
                                            new CommunityException(
                                                    CommunityErrorCode.POST_NOT_FOUND));

            validateBoardAccess(user, post.getBoard(), true);
            return;
        }

        Comment comment =
                commentRepository
                        .findByIdAndStatus(targetId, CommentStatus.ACTIVE)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.COMMENT_NOT_FOUND));

        validateBoardAccess(user, comment.getPost().getBoard(), false);
    }

    private void validateBoardAccess(User user, Board board, boolean postTarget) {
        if (board.getCategory() != BoardCategory.COHORT) {
            return;
        }

        // 해당하는 COHORT만 접근 가능
        if (user.getCohort() == null || board.getCategory() == null) {
            throw new CommunityException(
                    postTarget
                            ? CommunityErrorCode.POST_FORBIDDEN
                            : CommunityErrorCode.COMMENT_FORBIDDEN);
        }

        if (!user.getCohort().getId().equals(board.getCohort().getId())) {
            throw new CommunityException(
                    postTarget
                            ? CommunityErrorCode.POST_FORBIDDEN
                            : CommunityErrorCode.COMMENT_FORBIDDEN);
        }
    }

    public record ToggleReactionResult(
            String targetType,
            Long targetId,
            String reactionType,
            Boolean active,
            Integer likeCount,
            Integer dislikeCount) {}
}
