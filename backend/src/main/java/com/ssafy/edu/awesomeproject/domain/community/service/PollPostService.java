package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PollCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PollUpdateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PollVoteSubmitRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollUpdateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollVoteSubmitResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.PollPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.PollVote;
import com.ssafy.edu.awesomeproject.domain.community.entity.PollVoteOption;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PollPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PollVoteRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import java.time.LocalDateTime;
import java.util.Locale;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class PollPostService {
    private final UserRepository userRepository;
    private final BoardRepository boardRepository;
    private final PostRepository postRepository;
    private final PollPostRepository pollPostRepository;
    private final PollVoteRepository pollVoteRepository;

    public PollPostService(
            UserRepository userRepository,
            BoardRepository boardRepository,
            PostRepository postRepository,
            PollPostRepository pollPostRepository,
            PollVoteRepository pollVoteRepository) {
        this.userRepository = userRepository;
        this.boardRepository = boardRepository;
        this.postRepository = postRepository;
        this.pollPostRepository = pollPostRepository;
        this.pollVoteRepository = pollVoteRepository;
    }

    @Transactional
    public PollCreateResponseDto create(Long userId, PollCreateRequestDto pollCreateRequestDto) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));
        Board pollBoard =
                boardRepository
                        .findByCategory(BoardCategory.POLL)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));

        Post savedPost =
                postRepository.save(
                        new Post(
                                pollBoard,
                                user,
                                pollCreateRequestDto.title(),
                                pollCreateRequestDto.content()));

        pollPostRepository.save(
                new PollPost(
                        savedPost,
                        pollCreateRequestDto.question(),
                        pollCreateRequestDto.optionA(),
                        pollCreateRequestDto.optionB(),
                        pollCreateRequestDto.deadlineAt()));

        return new PollCreateResponseDto(savedPost.getId(), savedPost.getCreatedAt());
    }

    public PollDetailResponseDto detail(Long postId) {
        PollPost pollPost =
                pollPostRepository
                        .findByPost_Id(postId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POLL_NOT_FOUND));

        Post post = pollPost.getPost();
        long optionACount =
                pollVoteRepository.countByPostIdAndVoteOption(postId, PollVoteOption.OPTION_A);
        long optionBCount =
                pollVoteRepository.countByPostIdAndVoteOption(postId, PollVoteOption.OPTION_B);
        long totalVoteCount = pollVoteRepository.countByPostId(postId);
        boolean isClosed = pollPost.isClosed(LocalDateTime.now());

        return new PollDetailResponseDto(
                post.getId(),
                post.getTitle(),
                post.getContent(),
                post.getUser().getNickname(),
                pollPost.getQuestion(),
                pollPost.getOptionA(),
                pollPost.getOptionB(),
                pollPost.getDeadlineAt(),
                isClosed,
                optionACount,
                optionBCount,
                totalVoteCount,
                post.getCreatedAt(),
                post.getUpdatedAt());
    }

    @Transactional
    public PollUpdateResponseDto update(
            Long postId, Long userId, PollUpdateRequestDto pollUpdateRequestDto) {
        PollPost pollPost =
                pollPostRepository
                        .findByPost_Id(postId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POLL_NOT_FOUND));

        Post post = pollPost.getPost();
        if (!post.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.POST_FORBIDDEN);
        }

        post.update(pollUpdateRequestDto.title(), pollUpdateRequestDto.content());
        pollPost.update(
                pollUpdateRequestDto.question(),
                pollUpdateRequestDto.optionA(),
                pollUpdateRequestDto.optionB(),
                pollUpdateRequestDto.deadlineAt());

        return new PollUpdateResponseDto(post.getId(), post.getUpdatedAt());
    }

    @Transactional
    public PollVoteSubmitResponseDto vote(
            Long postId, Long userId, PollVoteSubmitRequestDto pollVoteSubmitRequestDto) {
        PollPost pollPost =
                pollPostRepository
                        .findByPost_Id(postId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.POLL_NOT_FOUND));
        validatePollOpen(pollPost);

        PollVoteOption voteOption = parseVoteOption(pollVoteSubmitRequestDto.voteOption());

        PollVote pollVote =
                pollVoteRepository
                        .findByPostIdAndUserId(postId, userId)
                        .map(
                                existingVote -> {
                                    existingVote.updateVoteOption(voteOption);
                                    return existingVote;
                                })
                        .orElseGet(() -> new PollVote(postId, userId, voteOption));

        PollVote savedVote = pollVoteRepository.save(pollVote);

        long optionACount =
                pollVoteRepository.countByPostIdAndVoteOption(postId, PollVoteOption.OPTION_A);
        long optionBCount =
                pollVoteRepository.countByPostIdAndVoteOption(postId, PollVoteOption.OPTION_B);
        long totalVoteCount = pollVoteRepository.countByPostId(postId);

        return new PollVoteSubmitResponseDto(
                postId,
                userId,
                savedVote.getVoteOption().name(),
                optionACount,
                optionBCount,
                totalVoteCount,
                savedVote.getUpdatedAt());
    }

    private void validatePollOpen(PollPost pollPost) {
        if (pollPost.isClosed(LocalDateTime.now())) {
            throw new CommunityException(CommunityErrorCode.POLL_NOT_OPEN);
        }
    }

    private PollVoteOption parseVoteOption(String voteOption) {
        try {
            return PollVoteOption.valueOf(voteOption.trim().toUpperCase(Locale.ROOT));
        } catch (RuntimeException exception) {
            throw new CommunityException(CommunityErrorCode.INVALID_INPUT);
        }
    }
}
