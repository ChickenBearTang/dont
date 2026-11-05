package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.HotdealCreateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.HotdealUpdateRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.HotdealCreateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.HotdealDetailResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.HotdealUpdateResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Board;
import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.HotdealPost;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.BoardRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.HotdealPostRepository;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class HotdealPostService {
    private final UserRepository userRepository;
    private final BoardRepository boardRepository;
    private final PostRepository postRepository;
    private final HotdealPostRepository hotdealPostRepository;
    private final PostAttachmentService postAttachmentService;
    private final S3AssetUrlResolver s3AssetUrlResolver;

    public HotdealPostService(
            UserRepository userRepository,
            BoardRepository boardRepository,
            PostRepository postRepository,
            HotdealPostRepository hotdealPostRepository,
            PostAttachmentService postAttachmentService,
            S3AssetUrlResolver s3AssetUrlResolver) {
        this.userRepository = userRepository;
        this.boardRepository = boardRepository;
        this.postRepository = postRepository;
        this.hotdealPostRepository = hotdealPostRepository;
        this.postAttachmentService = postAttachmentService;
        this.s3AssetUrlResolver = s3AssetUrlResolver;
    }

    @Transactional
    public HotdealCreateResponseDto create(
            Long userId, HotdealCreateRequestDto hotdealCreateRequestDto) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));
        Board hotdealBoard =
                boardRepository
                        .findByCategory(BoardCategory.HOTDEAL)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.BOARD_NOT_FOUND));

        Post savedPost =
                postRepository.save(
                        new Post(
                                hotdealBoard,
                                user,
                                hotdealCreateRequestDto.title(),
                                hotdealCreateRequestDto.content()));
        postAttachmentService.syncAttachments(savedPost, hotdealCreateRequestDto.attachments());

        hotdealPostRepository.save(toEntity(savedPost, hotdealCreateRequestDto));

        return new HotdealCreateResponseDto(savedPost.getId(), savedPost.getCreatedAt());
    }

    public HotdealDetailResponseDto detail(Long postId) {
        HotdealPost hotdealPost =
                hotdealPostRepository
                        .findByPost_Id(postId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.HOTDEAL_NOT_FOUND));

        Post post = hotdealPost.getPost();
        // 이 조회는 로그인 없이 열려 있다. 일반 조회(PostService#getPost)와 같게, 삭제된 글은 없는 글로 보고 신고로
        // 가려진 글은 내용 없이 안내 문구만 준다. 예전에는 글 상태를 보지 않아 둘 다 내용이 그대로 나갔다.
        if (post.getStatus() == PostStatus.DELETED) {
            throw new CommunityException(CommunityErrorCode.HOTDEAL_NOT_FOUND);
        }
        boolean blinded = post.getStatus() == PostStatus.BLINDED;
        return new HotdealDetailResponseDto(
                post.getId(),
                blinded ? PostService.BLINDED_POST_MESSAGE : post.getTitle(),
                blinded ? PostService.BLINDED_POST_MESSAGE : post.getContent(),
                post.getUser().getId(),
                post.getUser().getNickname(),
                s3AssetUrlResolver.resolvePublicUrlOrNull(post.getUser().getProfileImageUrl()),
                blinded ? PostService.BLINDED_POST_MESSAGE : hotdealPost.getProductName(),
                blinded ? null : hotdealPost.getStoreName(),
                hotdealPost.getDealPriceAmount(),
                hotdealPost.getOriginalPriceAmount(),
                blinded ? null : hotdealPost.getDealUrl(),
                blinded ? null : hotdealPost.getShippingInfo(),
                hotdealPost.getExpiredAt(),
                blinded ? List.of() : postAttachmentService.getAttachments(post.getId()),
                post.getCreatedAt(),
                post.getUpdatedAt());
    }

    @Transactional
    public HotdealUpdateResponseDto update(
            Long postId, Long userId, HotdealUpdateRequestDto hotdealUpdateRequestDto) {
        HotdealPost hotdealPost =
                hotdealPostRepository
                        .findByPost_Id(postId)
                        .orElseThrow(
                                () -> new CommunityException(CommunityErrorCode.HOTDEAL_NOT_FOUND));

        Post post = hotdealPost.getPost();
        if (!post.isAuthor(userId)) {
            throw new CommunityException(CommunityErrorCode.POST_FORBIDDEN);
        }

        post.update(hotdealUpdateRequestDto.title(), hotdealUpdateRequestDto.content());
        postAttachmentService.syncAttachments(post, hotdealUpdateRequestDto.attachments());
        hotdealPost.update(
                hotdealUpdateRequestDto.productName(),
                hotdealUpdateRequestDto.storeName(),
                hotdealUpdateRequestDto.dealPriceAmount(),
                hotdealUpdateRequestDto.originalPriceAmount(),
                hotdealUpdateRequestDto.dealUrl(),
                hotdealUpdateRequestDto.shippingInfo(),
                hotdealUpdateRequestDto.expiredAt());

        return new HotdealUpdateResponseDto(post.getId(), post.getUpdatedAt());
    }

    private HotdealPost toEntity(Post post, HotdealCreateRequestDto hotdealCreateRequestDto) {
        return new HotdealPost(
                post,
                hotdealCreateRequestDto.productName(),
                hotdealCreateRequestDto.storeName(),
                hotdealCreateRequestDto.dealPriceAmount(),
                hotdealCreateRequestDto.originalPriceAmount(),
                hotdealCreateRequestDto.dealUrl(),
                hotdealCreateRequestDto.shippingInfo(),
                hotdealCreateRequestDto.expiredAt());
    }
}
