package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Reaction;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionTargetType;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionType;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReactionRepository extends JpaRepository<Reaction, Long> {
    Optional<Reaction> findByUser_IdAndTargetTypeAndTargetIdAndReactionType(
            Long userId, ReactionTargetType targetType, Long targetId, ReactionType reactionType);

    long countByTargetTypeAndTargetIdAndReactionType(
            ReactionTargetType targetType, Long targetId, ReactionType reactionType);
}
