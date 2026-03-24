package com.ssafy.edu.awesomeproject.domain.community.controller;

import com.ssafy.edu.awesomeproject.common.annotation.ApiCommonResponses;
import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.community.dto.request.AttachmentPresignRequestDto;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.AttachmentPresignResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.service.PostAttachmentService;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/community/attachments")
public class CommunityAttachmentController {
    private final PostAttachmentService postAttachmentService;

    public CommunityAttachmentController(PostAttachmentService postAttachmentService) {
        this.postAttachmentService = postAttachmentService;
    }

    @PostMapping("/presign")
    @ApiCommonResponses
    @Operation(summary = "커뮤니티 첨부 업로드 URL 발급 API", description = "게시글 첨부 업로드용 presigned URL 목록을 발급합니다.")
    public CommonResponse<AttachmentPresignResponseDto> createUploadUrls(
            @CurrentUserId Long userId, @Valid @RequestBody AttachmentPresignRequestDto request) {
        return CommonResponse.success(postAttachmentService.createUploadUrls(userId, request.files()));
    }
}
