package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.Reaction;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionTargetType;
import com.ssafy.edu.awesomeproject.domain.community.entity.ReactionType;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ReactionRepository extends JpaRepository<Reaction, Long> {
    Optional<Reaction> findByUser_IdAndTargetTypeAndTargetIdAndReactionType(
            Long userId, ReactionTargetType targetType, Long targetId, ReactionType reactionType);

    long countByTargetTypeAndTargetIdAndReactionType(
            ReactionTargetType targetType, Long targetId, ReactionType reactionType);

    @Query("""
            select r.targetId as targetId, count(r) as reactionCount
            from Reaction r
            where r.targetType = :targetType
              and r.reactionType = :reactionType
              and r.targetId in :targetIds
            group by r.targetId
            """)
    List<ReactionCountProjection> aggregateByTargetTypeAndReactionTypeAndTargetIdIn(
            @Param("targetType") ReactionTargetType targetType,
            @Param("reactionType") ReactionType reactionType,
            @Param("targetIds") Collection<Long> targetIds);

    interface ReactionCountProjection {
        Long getTargetId();

        Long getReactionCount();
    }
}
