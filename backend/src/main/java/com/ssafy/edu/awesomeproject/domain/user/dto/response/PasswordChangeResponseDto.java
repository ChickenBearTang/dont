package com.ssafy.edu.awesomeproject.domain.user.dto.response;

public record PasswordChangeResponseDto(boolean passwordChanged, boolean reLoginRequired) {}
