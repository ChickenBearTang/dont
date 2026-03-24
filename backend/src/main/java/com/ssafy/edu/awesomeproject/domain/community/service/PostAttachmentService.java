package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.UploadFileCommand;
import com.ssafy.edu.awesomeproject.common.s3.dto.response.PresignedUrlResponse;
import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.common.s3.service.S3FileTemplateService;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.AttachmentPresignFileRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.PostAttachmentRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.AttachmentPresignFileResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.AttachmentPresignResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PostAttachmentResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostAttachment;
import com.ssafy.edu.awesomeproject.domain.community.repository.PostAttachmentRepository;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class PostAttachmentService {
    private static final Set<String> ALLOWED_CONTENT_TYPES =
            Set.of(
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                    "application/pdf");
    private static final Set<String> ALLOWED_EXTENSIONS =
            Set.of("jpg", "jpeg", "png", "webp", "pdf");
    private static final String ATTACHMENT_PURPOSE_PREFIX = "community-post-attachment-user-";

    private final UserRepository userRepository;
    private final PostAttachmentRepository postAttachmentRepository;
    private final S3FileTemplateService s3FileTemplateService;
    private final S3AssetUrlResolver s3AssetUrlResolver;

    public PostAttachmentService(
            UserRepository userRepository,
            PostAttachmentRepository postAttachmentRepository,
            S3FileTemplateService s3FileTemplateService,
            S3AssetUrlResolver s3AssetUrlResolver) {
        this.userRepository = userRepository;
        this.postAttachmentRepository = postAttachmentRepository;
        this.s3FileTemplateService = s3FileTemplateService;
        this.s3AssetUrlResolver = s3AssetUrlResolver;
    }

    public AttachmentPresignResponseDto createUploadUrls(
            Long userId, List<AttachmentPresignFileRequestDto> files) {
        validateUserExists(userId);
        if (files == null || files.isEmpty()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "files must not be empty.");
        }

        List<UploadFileCommand> uploadFiles = new ArrayList<>(files.size());
        for (AttachmentPresignFileRequestDto file : files) {
            validateFile(file.fileName(), file.contentType());
            uploadFiles.add(new UploadFileCommand(file.fileName(), normalizeContentType(file.contentType()), file.contentLength()));
        }

        List<PresignedUrlResponse> responses =
                s3FileTemplateService.createPublicUploadUrls(buildPurpose(userId), uploadFiles, null);

        List<AttachmentPresignFileResponseDto> result =
                responses.stream()
                        .map(
                                response ->
                                        new AttachmentPresignFileResponseDto(
                                                response.url(),
                                                response.method(),
                                                response.headers(),
                                                response.key(),
                                                response.expiresAt(),
                                                s3AssetUrlResolver.resolvePublicUrlOrNull(response.key())))
                        .toList();

        return new AttachmentPresignResponseDto(result);
    }

    @Transactional
    public void syncAttachments(Post post, List<PostAttachmentRequestDto> attachments) {
        List<PostAttachmentRequestDto> normalized = attachments == null ? List.of() : attachments;
        validateAttachmentRequests(post.getUser().getId(), normalized);

        postAttachmentRepository.deleteByPostId(post.getId());
        if (normalized.isEmpty()) {
            return;
        }

        List<PostAttachment> entities = new ArrayList<>(normalized.size());
        for (int index = 0; index < normalized.size(); index++) {
            PostAttachmentRequestDto attachment = normalized.get(index);
            entities.add(
                    new PostAttachment(
                            post,
                            normalizeKey(attachment.key()),
                            attachment.fileName().trim(),
                            normalizeContentType(attachment.contentType()),
                            attachment.fileSize(),
                            index));
        }
        postAttachmentRepository.saveAll(entities);
    }

    public List<PostAttachmentResponseDto> getAttachments(Long postId) {
        return postAttachmentRepository.findAllByPost_IdOrderByDisplayOrderAscIdAsc(postId).stream()
                .map(this::toResponse)
                .toList();
    }

    public Map<Long, List<PostAttachmentResponseDto>> getAttachmentsByPostIds(Collection<Long> postIds) {
        if (postIds == null || postIds.isEmpty()) {
            return Map.of();
        }

        return postAttachmentRepository.findAllByPost_IdInOrderByPost_IdAscDisplayOrderAscIdAsc(postIds).stream()
                .collect(
                        Collectors.groupingBy(
                                attachment -> attachment.getPost().getId(),
                                Collectors.mapping(this::toResponse, Collectors.toList())));
    }

    public Map<Long, Integer> getAttachmentCountByPostIds(Collection<Long> postIds) {
        if (postIds == null || postIds.isEmpty()) {
            return Map.of();
        }

        return postAttachmentRepository.countByPostIds(postIds).stream()
                .collect(
                        Collectors.toMap(
                                PostAttachmentRepository.PostAttachmentCountProjection::getPostId,
                                projection -> Math.toIntExact(projection.getAttachmentCount())));
    }

    private PostAttachmentResponseDto toResponse(PostAttachment attachment) {
        return new PostAttachmentResponseDto(
                attachment.getId(),
                attachment.getFileKey(),
                attachment.getOriginalFileName(),
                attachment.getContentType(),
                attachment.getFileSize(),
                s3AssetUrlResolver.resolvePublicUrlOrNull(attachment.getFileKey()));
    }

    private void validateAttachmentRequests(Long userId, List<PostAttachmentRequestDto> attachments) {
        Set<String> keys = new LinkedHashSet<>();
        for (PostAttachmentRequestDto attachment : attachments) {
            if (attachment == null) {
                throw new CommonException(CommonErrorCode.INVALID_INPUT, "attachment must not be null.");
            }
            validateFile(attachment.fileName(), attachment.contentType());
            String normalizedKey = normalizeKey(attachment.key());
            validateAttachmentKey(userId, normalizedKey);
            if (!keys.add(normalizedKey)) {
                throw new CommonException(CommonErrorCode.INVALID_INPUT, "duplicate attachment key.");
            }
        }
    }

    private void validateUserExists(Long userId) {
        if (userId == null || !userRepository.existsById(userId)) {
            throw new CommonException(CommonErrorCode.RESOURCE_NOT_FOUND, "user not found.");
        }
    }

    private void validateFile(String fileName, String contentType) {
        String normalizedContentType = normalizeContentType(contentType);
        if (!ALLOWED_CONTENT_TYPES.contains(normalizedContentType)) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "unsupported content type.");
        }

        String extension = extractExtension(fileName);
        if (!ALLOWED_EXTENSIONS.contains(extension)) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "unsupported file extension.");
        }
    }

    private String extractExtension(String fileName) {
        if (fileName == null || fileName.isBlank()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "fileName is required.");
        }
        int dotIndex = fileName.lastIndexOf('.');
        if (dotIndex < 0 || dotIndex == fileName.length() - 1) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "invalid file name.");
        }
        return fileName.substring(dotIndex + 1).toLowerCase(Locale.ROOT);
    }

    private void validateAttachmentKey(Long userId, String key) {
        String expectedPrefix = "public/community-post-attachment/" + userId + "/";
        if (!key.startsWith(expectedPrefix)) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "invalid attachment key.");
        }
    }

    private String buildPurpose(Long userId) {
        return ATTACHMENT_PURPOSE_PREFIX + userId;
    }

    private String normalizeContentType(String contentType) {
        if (contentType == null) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "contentType is required.");
        }
        return contentType.trim().toLowerCase(Locale.ROOT);
    }

    private String normalizeKey(String key) {
        if (key == null) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "key is required.");
        }
        return key.trim();
    }
}
