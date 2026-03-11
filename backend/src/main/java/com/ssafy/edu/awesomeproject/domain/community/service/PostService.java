package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Service
@Transactional
public class PostService {
    private final PostRepository postRepository;
    private final BoardRepository boardRepository;
    private final UserRepository userRepository;

    public PostService(PostRepository postRepository, BoardRepository boardRepository, UserRepository userRepository) {
        this.postRepository = postRepository;
        this.boardRepository = boardRepository;
        this.userRepository = userRepository;
    }

    //게시글 생성
    public CreatePostResult createPost(Long userId, String category, String title, String content) {
        Board board = boardRepository.findByCategory(category)
            .orElseThrow(() -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));

        // 게시판 작성하려는 user 불러옴
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new AuthException(CommunityErrorCode.USER_NOT_FOUND));

        Post post = new Post(board, user, title, content);
        Post savedPost = postRepository.save(post);

        return new CreatePostResult(
            savedPost.getId(),
            savedPost.getBoard().getCategory(),
            savedPost.getCreatedAt()
        );
    }

    //게시글 조회 (postId로)
    @Transactional(readOnly = true)
    public GetPostResult getPost(Long postId) {
        Post post = postRepository.findByIdAndStatus(postId, PostStatus.ACTIVE)
            .orElseThrow(() -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        //받아오는 결과
        //게시글id, 카테고리(기수별, pr), 제목, 내용, 작성한사람 닉네임
        //TODO: dislike, like, comment는 추후 변경할 예정
        return new GetPostResult(
            post.getId(),
            post.getBoard().getCategory(),
            post.getTitle(),
            post.getContent(),
            post.getUser().getNickname(),
            0,
            0,
            0,
            post.getCreatedAt(),
            post.getUpdatedAt()
        );
    }

    //게시글 수정
    public UpdatePostResult updatePost(Long userId, Long postId, String title, String content) {
        //게시글이 존재해야 update 가능
        Post post = postRepository.findByIdAndStatus(postId, PostStatus.ACTIVE)
            .orElseThrow(() -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        if (!post.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.POST_FORBIDDEN);
        }

        post.update(title, content);

        return new UpdatePostResult(post.getId(), post.getUpdatedAt());
    }

    //게시글 삭제
    public DeletePostResult deletePost(Long userId, Long postId) {
        Post post = postRepository.findByIdAndStatus(postId, PostStatus.ACTIVE)
            .orElseThrow(() -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        if (!post.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.POST_FORBIDDEN);
        }

        post.delete();

        return new DeletePostResult(true, post.getDeletedAt());
    }

    public record CreatePostResult(Long postId, String category, LocalDateTime createdAt) {}

    public record GetPostResult(
        Long postId,
        String category,
        String title,
        String content,
        String authorNickname,
        Integer likeCount,
        Integer dislikeCount,
        Integer commentCount,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}

    public record UpdatePostResult(Long postId, LocalDateTime updatedAt) {}

    public record DeletePostResult(Boolean deleted, LocalDateTime deletedAt) {}
}
