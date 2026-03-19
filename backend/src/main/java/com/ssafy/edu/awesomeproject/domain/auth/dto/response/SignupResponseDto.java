package com.ssafy.edu.awesomeproject.domain.auth.dto.response;

public record SignupResponseDto(Long userId, String email, String userRole, Integer generationNo) {}
