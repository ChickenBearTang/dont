package com.ssafy.edu.awesomeproject.domain.community.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.HotdealDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PollDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PostAttachmentResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.HotdealPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.PollPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.HotdealPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PollPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PollVoteRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

/**
 * 핫딜·토론 상세 조회는 로그인 없이 열려 있다. 그래서 일반 조회(PostService#getPost)와 같이 글 상태를 지켜야 한다:
 * 삭제된 글은 없는 글이고, 신고로 가려진 글은 내용 없이 안내 문구만 나간다.
 *
 * <p>예전에는 상태를 보지 않아서 작성자가 지운 글과 관리자가 가린 글의 제목·내용·링크·첨부가 누구에게나 그대로
 * 나갔다 (실제 서버로 재현했다).
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class PublicPostDetailVisibilityTest {

    private static final String SECRET = "작성자가 지웠거나 관리자가 가린 내용";
    private static final String SECRET_LINK = "https://secret.example/deal";
    private static final String BLINDED = "신고 처리된 게시물입니다.";

    @Mock private UserRepository userRepository;
    @Mock private BoardRepository boardRepository;
    @Mock private PostRepository postRepository;
    @Mock private HotdealPostRepository hotdealPostRepository;
    @Mock private PollPostRepository pollPostRepository;
    @Mock private PollVoteRepository pollVoteRepository;
    @Mock private PostAttachmentService postAttachmentService;
    @Mock private S3AssetUrlResolver s3AssetUrlResolver;

    private HotdealPostService hotdealService;
    private PollPostService pollService;

    @BeforeEach
    void setUp() {
        hotdealService =
                new HotdealPostService(
                        userRepository, boardRepository, postRepository, hotdealPostRepository,
                        postAttachmentService, s3AssetUrlResolver);
        pollService =
                new PollPostService(
                        userRepository, boardRepository, postRepository, pollPostRepository, pollVoteRepository,
                        postAttachmentService, s3AssetUrlResolver);
        when(postAttachmentService.getAttachments(10L))
                .thenReturn(List.of(new PostAttachmentResponseDto(1L, "public/a.png", "a.png", "image/png", 3L, "https://cdn/a.png")));
    }

    private Post post(PostStatus status) {
        User author = mock(User.class);
        when(author.getId()).thenReturn(5L);
        when(author.getNickname()).thenReturn("작성자");
        Post post = mock(Post.class);
        when(post.getId()).thenReturn(10L);
        when(post.getStatus()).thenReturn(status);
        when(post.getTitle()).thenReturn(SECRET);
        when(post.getContent()).thenReturn(SECRET);
        when(post.getUser()).thenReturn(author);
        when(post.getCreatedAt()).thenReturn(LocalDateTime.of(2026, 1, 1, 0, 0));
        return post;
    }

    private void hotdeal(PostStatus status) {
        Post post = post(status); // 중첩 stubbing 을 피하려고 먼저 만든다
        HotdealPost hotdeal = mock(HotdealPost.class);
        when(hotdeal.getPost()).thenReturn(post);
        when(hotdeal.getProductName()).thenReturn(SECRET);
        when(hotdeal.getStoreName()).thenReturn(SECRET);
        when(hotdeal.getDealPriceAmount()).thenReturn(10_000L);
        when(hotdeal.getOriginalPriceAmount()).thenReturn(20_000L);
        when(hotdeal.getDealUrl()).thenReturn(SECRET_LINK);
        when(hotdeal.getShippingInfo()).thenReturn(SECRET);
        when(hotdealPostRepository.findByPost_Id(10L)).thenReturn(Optional.of(hotdeal));
    }

    private void poll(PostStatus status) {
        Post post = post(status);
        PollPost poll = mock(PollPost.class);
        when(poll.getPost()).thenReturn(post);
        when(poll.getQuestion()).thenReturn(SECRET);
        when(poll.getOptionA()).thenReturn(SECRET);
        when(poll.getOptionB()).thenReturn(SECRET);
        when(pollPostRepository.findByPost_Id(10L)).thenReturn(Optional.of(poll));
        when(pollVoteRepository.countByPostId(10L)).thenReturn(7L);
    }

    @Test
    void anActiveHotdealIsShownInFull() {
        hotdeal(PostStatus.ACTIVE);

        HotdealDetailResponseDto dto = hotdealService.detail(10L);

        assertThat(dto.title()).isEqualTo(SECRET);
        assertThat(dto.dealUrl()).isEqualTo(SECRET_LINK);
        assertThat(dto.attachments()).hasSize(1);
    }

    @Test
    void aDeletedHotdealDoesNotExistForTheCaller() {
        hotdeal(PostStatus.DELETED);

        assertThatThrownBy(() -> hotdealService.detail(10L))
                .isInstanceOfSatisfying(
                        CommonException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(CommunityErrorCode.HOTDEAL_NOT_FOUND));
    }

    @Test
    void aBlindedHotdealShowsOnlyTheNoticeNotTheContentTheLinkOrTheAttachments() {
        hotdeal(PostStatus.BLINDED);

        HotdealDetailResponseDto dto = hotdealService.detail(10L);

        assertThat(dto.title()).isEqualTo(BLINDED);
        assertThat(dto.content()).isEqualTo(BLINDED);
        assertThat(dto.productName()).isEqualTo(BLINDED);
        assertThat(dto.dealUrl()).isNull();
        assertThat(dto.storeName()).isNull();
        assertThat(dto.shippingInfo()).isNull();
        assertThat(dto.attachments()).isEmpty();
        assertThat(dto.toString()).doesNotContain(SECRET).doesNotContain(SECRET_LINK);
        verify(postAttachmentService, never()).getAttachments(10L);
    }

    @Test
    void anActivePollIsShownInFull() {
        poll(PostStatus.ACTIVE);

        PollDetailResponseDto dto = pollService.detail(10L);

        assertThat(dto.question()).isEqualTo(SECRET);
        assertThat(dto.optionA()).isEqualTo(SECRET);
        assertThat(dto.attachments()).hasSize(1);
    }

    @Test
    void aDeletedPollDoesNotExistForTheCaller() {
        poll(PostStatus.DELETED);

        assertThatThrownBy(() -> pollService.detail(10L))
                .isInstanceOfSatisfying(
                        CommonException.class,
                        e -> assertThat(e.getErrorCode()).isEqualTo(CommunityErrorCode.POLL_NOT_FOUND));
    }

    @Test
    void aBlindedPollShowsOnlyTheNoticeButKeepsTheVoteCounts() {
        poll(PostStatus.BLINDED);

        PollDetailResponseDto dto = pollService.detail(10L);

        assertThat(dto.title()).isEqualTo(BLINDED);
        assertThat(dto.content()).isEqualTo(BLINDED);
        assertThat(dto.question()).isEqualTo(BLINDED);
        assertThat(dto.optionA()).isEqualTo("선택지 A");
        assertThat(dto.optionB()).isEqualTo("선택지 B");
        assertThat(dto.attachments()).isEmpty();
        assertThat(dto.totalVoteCount()).isEqualTo(7L);
        assertThat(dto.toString()).doesNotContain(SECRET);
        verify(postAttachmentService, never()).getAttachments(10L);
    }
}
