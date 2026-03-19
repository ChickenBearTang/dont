package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

// 게시글 생성할 때 어떤 기수(ex. 14기) 인지 필요
// request에 cohortId 추가
public record CreatePostRequestDto(
        @NotNull BoardCategory category,
        Integer generationNo,
        @NotNull @Size(max = 200) String title,
        @NotNull String content) {}
