package com.ssafy.edu.awesomeproject.domain.user.dto.response;

public record ProfileImageDeleteResponseDto(
        boolean deleted, String profileImageKey, String profileImageUrl) {}
