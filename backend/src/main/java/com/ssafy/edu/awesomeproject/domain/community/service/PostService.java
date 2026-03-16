package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.error.AuthException;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrStatus;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.CohortRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrVoteRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@Transactional
public class PostService {
    private final PostRepository postRepository;
    private final BoardRepository boardRepository;
    private final UserRepository userRepository;
    private final CohortRepository cohortRepository;
    private final PrPostRepository prPostRepository;
    private final PrVoteRepository prVoteRepository;

    public PostService(
            PostRepository postRepository,
            BoardRepository boardRepository,
            CohortRepository cohortRepository,
            UserRepository userRepository,
            PrPostRepository prPostRepository,
            PrVoteRepository prVoteRepository) {
        this.postRepository = postRepository;
        this.boardRepository = boardRepository;
        this.cohortRepository = cohortRepository;
        this.userRepository = userRepository;
        this.prPostRepository = prPostRepository;
        this.prVoteRepository = prVoteRepository;
    }

    //게시글 생성
    public CreatePostResult createPost(
        Long userId,
        BoardCategory category,
        Integer generationNo,
        String title,
        String content) {
        validateCategoryAndCohort(category, generationNo);

        Board board = resolveBoard(category, generationNo);

        // 게시판 작성하려는 user 불러옴
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new AuthException(CommunityErrorCode.USER_NOT_FOUND));

        if(category == BoardCategory.COHORT) {
            validateUserCohort(user, generationNo);
        }

        Post post = new Post(board, user, title, content);
        Post savedPost = postRepository.save(post);

        return new CreatePostResult(
            savedPost.getId(),
            savedPost.getBoard().getCategory().name(),
            extractGenerationNo(savedPost.getBoard()),
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
            extractGenerationNo(post.getBoard()),
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
    public GetPostListResult getPostsByCategory(BoardCategory category, Integer generationNo, Integer page, Integer size) {
        int pageNumber = (page == null || page < 0) ? 0 : page;
        int pageSize = (size == null || size <= 0) ? 5 : size;

        if (category != null) {
            validateCategoryAndCohort(category, generationNo);
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
            postPage = postRepository.findByBoard_CategoryAndBoard_Cohort_GenerationNoAndStatus(
                category,
                generationNo,
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

        Map<Long, PrPost> prByPostId = getPrByPostId(postPage.getContent(), category);
        Map<Long, PrVoteSummary> voteSummaryByPostId = getPrVoteSummaryByPostId(postPage.getContent(), category);

        List<PostSummary> content = postPage.getContent().stream()
            .map(post -> {
                PrSummary prSummary =
                    buildPrSummary(prByPostId, voteSummaryByPostId, post.getId());

                return new PostSummary(
                    post.getId(),
                    post.getBoard().getCategory().name(),
                    extractGenerationNo(post.getBoard()),
                    post.getTitle(),
                    post.getUser().getNickname(),
                    0,
                    0,
                    post.getCreatedAt(),
                    prSummary != null ? new PostExtraSummary(prSummary) : null
                );
            })
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

    private Board resolveBoard(BoardCategory category, Integer generationNo) {
        if (category == BoardCategory.COHORT) {
            cohortRepository.findByGenerationNo(generationNo)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.COHORT_NOT_FOUND));

            return boardRepository.findByCategoryAndCohort_GenerationNo(category, generationNo)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));
        }

        return boardRepository.findByCategory(category)
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

    private Map<Long, PrPost> getPrByPostId(List<Post> posts, BoardCategory category) {
        if (posts.isEmpty() || category != BoardCategory.PR) {
            return Map.of();
        }

        Set<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toSet());
        return prPostRepository.findByPostIdIn(postIds).stream()
            .collect(Collectors.toMap(PrPost::getPostId, Function.identity()));
    }

    private Map<Long, PrVoteSummary> getPrVoteSummaryByPostId(List<Post> posts, BoardCategory category) {
        if (posts.isEmpty() || category != BoardCategory.PR) {
            return Map.of();
        }

        Set<Long> postIds = posts.stream().map(Post::getId).collect(Collectors.toSet());
        return prVoteRepository.aggregateByPostIds(postIds).stream()
            .collect(
                Collectors.toMap(
                    PrVoteRepository.PrVoteCountProjection::getPostId,
                    projection ->
                        new PrVoteSummary(
                            projection.getTotalVoteCount()
                        )
                )
            );
    }

    private String getStatus(Map<Long, PrPost> prByPostId, Long postId) {
        PrPost prPost = prByPostId.get(postId);
        if (prPost == null) {
            return null;
        }

        return prPost.getResultStatusEnum() == PrStatus.OPEN ? PrStatus.OPEN.name() : PrStatus.CLOSED.name();
    }

    private String getResultStatus(Map<Long, PrPost> prByPostId, Long postId) {
        PrPost prPost = prByPostId.get(postId);
        return prPost != null ? prPost.getResultStatus() : null;
    }

    private Long getTotalVoteCount(Map<Long, PrVoteSummary> voteSummaryByPostId, Long postId) {
        PrVoteSummary summary = voteSummaryByPostId.get(postId);
        return summary != null ? summary.totalVoteCount() : null;
    }

    private LocalDateTime getDeadlineAt(Map<Long, PrPost> prByPostId, Long postId) {
        PrPost prPost = prByPostId.get(postId);
        return prPost != null ? prPost.getDeadlineAt() : null;
    }

    private PrSummary buildPrSummary(
            Map<Long, PrPost> prByPostId,
            Map<Long, PrVoteSummary> voteSummaryByPostId,
            Long postId) {
        PrPost prPost = prByPostId.get(postId);
        if (prPost == null) {
            return null;
        }

        return new PrSummary(
                getStatus(prByPostId, postId),
                getResultStatus(prByPostId, postId),
                getTotalVoteCount(voteSummaryByPostId, postId),
                getDeadlineAt(prByPostId, postId));
    }

    public record CreatePostResult(
        Long postId,
        String category,
        Integer generationNo,
        LocalDateTime createdAt
    ) {}

    public record GetPostResult(
        Long postId,
        String category,
        Integer generationNo,
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
        Integer  generationNo,
        String title,
        String authorNickname,
        Integer likeCount,
        Integer commentCount,
        LocalDateTime createdAt,
        PostExtraSummary extraSummary
    ) {}

    private record PrVoteSummary(Long totalVoteCount) {}

    public record PostExtraSummary(
        PrSummary pr
    ) {}

    public record PrSummary(
        String status,
        String resultStatus,
        Long totalVoteCount,
        LocalDateTime deadlineAt
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
