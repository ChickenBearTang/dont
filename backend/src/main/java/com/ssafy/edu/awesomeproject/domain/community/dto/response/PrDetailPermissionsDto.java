package com.ssafy.edu.awesomeproject.domain.community.dto.response;

public record PrDetailPermissionsDto(
        boolean canVote, boolean canClose, String voteDisabledReason, String closeDisabledReason) {}
