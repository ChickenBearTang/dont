package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

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
    public CreatePostResult createPost(
        Long userId,
        BoardCategory category,
        Long cohortId,
        String title,
        String content) {
        validateCategoryAndCohort(category, cohortId);

        Board board = resolveBoard(category, cohortId);

        // 게시판 작성하려는 user 불러옴
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new AuthException(CommunityErrorCode.USER_NOT_FOUND));

        Post post = new Post(board, user, title, content);
        Post savedPost = postRepository.save(post);

        return new CreatePostResult(
            savedPost.getId(),
            savedPost.getBoard().getCategory().name(),
            savedPost.getBoard().getCohortId(),
            savedPost.getCreatedAt()
        );
    }

    //게시글 상세 조회
    //postId가 PK라 카테고리 명시하지 않아도 하나씩만 조회됨
    @Transactional(readOnly = true)
    public GetPostResult getPost(Long postId) {
        Post post = postRepository.findByIdAndStatus(postId, PostStatus.ACTIVE)
            .orElseThrow(() -> new CommunityException(CommunityErrorCode.POST_NOT_FOUND));

        //받아오는 결과
        //게시글id, 카테고리(기수별, pr), 제목, 내용, 작성한사람 닉네임
        //TODO: dislike, like, comment는 추후 변경할 예정
        return new GetPostResult(
            post.getId(),
            post.getBoard().getCategory().name(),
            post.getBoard().getCohortId(),
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

    //게시글 목록 조회 -> 페이지 번호 방식으로
    //page는 현재 바라보고 있는 페이지
    //size는 총 페이지
    @Transactional(readOnly = true)
    public GetPostListResult getPostsByCategory(BoardCategory category, Long cohortId, Integer page, Integer size) {
        int pageNumber = (page == null || page < 0) ? 0 : page;
        int pageSize = (size == null || size <= 0) ? 5 : size;

        if (category != null) {
            validateCategoryAndCohortForSearch(category, cohortId);
        }
        PageRequest pageRequest = PageRequest.of(
            pageNumber,
            pageSize,
            Sort.by(Sort.Direction.DESC, "id")
        );

        Page<Post> postPage;
        if (category == null) {
            postPage = postRepository.findByStatus(PostStatus.ACTIVE, pageRequest);
            //조회하려는 게시판이 기수 게시판이면
        } else if (category == BoardCategory.COHORT){
            postPage = postRepository.findByBoard_CategoryAndBoard_CohortIdAndStatus(
                category,
                cohortId,
                PostStatus.ACTIVE,
                pageRequest
            );
        } else {
            postPage = postRepository.findByBoard_CategoryAndStatus(
                category,
                PostStatus.ACTIVE,
                pageRequest
            );
        }

        List<PostSummary> content = postPage.getContent().stream()
            .map(post -> new PostSummary(
                post.getId(),
                post.getBoard().getCategory().name(),
                post.getBoard().getCohortId(),
                post.getTitle(),
                post.getUser().getNickname(),
                0,
                0,
                post.getCreatedAt()
            ))
            .toList();

        return new GetPostListResult(
            content,
            postPage.getNumber(),
            postPage.getSize(),
            postPage.getTotalElements(),
            postPage.getTotalPages(),
            postPage.hasNext()
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

    private Board resolveBoard(BoardCategory category, Long cohortId) {
        //category == cohort 일 때
        if (category == BoardCategory.COHORT) {
            return boardRepository.findByCategoryAndCohortId(category, cohortId)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));
        }
        //아닐 때
        return boardRepository.findByCategory(category)
            .orElseThrow(() -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));
    }

    private void validateCategoryAndCohort(BoardCategory category, Long cohortId) {
        //category == cohort 인데 cohortId 없을 때
        if (category == BoardCategory.COHORT && cohortId == null) {
            throw new CommunityException(CommunityErrorCode.COHORT_ID_REQUIRED);
        }
        //category != cohort 인데 cohortId 있을 때
        if (category != BoardCategory.COHORT && cohortId != null) {
            throw new  CommunityException(CommunityErrorCode.INVALID_CATEGORY_AND_COHORT);
        }
    }

    private void validateCategoryAndCohortForSearch(BoardCategory category, Long cohortId) {
        if (category == BoardCategory.COHORT && cohortId == null) {
            throw  new CommunityException(CommunityErrorCode.COHORT_ID_REQUIRED);
        }

        if (category != BoardCategory.COHORT && cohortId != null) {
            throw new  CommunityException(CommunityErrorCode.INVALID_CATEGORY_AND_COHORT);
        }
    }

    public record CreatePostResult(
        Long postId,
        String category,
        Long cohortId,
        LocalDateTime createdAt
    ) {}

    public record GetPostResult(
        Long postId,
        String category,
        Long cohortId,
        String title,
        String content,
        String authorNickname,
        Integer likeCount,
        Integer dislikeCount,
        Integer commentCount,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}

    public record PostSummary(
        Long postId,
        String category,
        Long cohortId,
        String title,
        String authorNickname,
        Integer likeCount,
        Integer commentCount,
        LocalDateTime createdAt
    ) {}

    public record GetPostListResult(
        List<PostSummary> content,
        int page,
        int size,
        long totalElements,
        int totalPages,
        boolean hasNext
    ) {}

    public record UpdatePostResult(Long postId, LocalDateTime updatedAt) {}

    public record DeletePostResult(Boolean deleted, LocalDateTime deletedAt) {}
}
