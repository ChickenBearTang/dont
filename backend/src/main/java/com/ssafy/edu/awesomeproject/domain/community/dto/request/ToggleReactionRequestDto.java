package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionTargetType;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionType;
import jakarta.validation.constraints.NotNull;

public record ToggleReactionRequestDto(

        @NotNull(message = "targetType은 필수입니다.") ReactionTargetType targetType,


        @NotNull(message = "targetId는 필수입니다.") Long targetId,


        @NotNull(message = "reactionType은 필수입니다.") ReactionType reactionType,
        @NotNull(message = "active는 필수입니다.") Boolean active) {}
