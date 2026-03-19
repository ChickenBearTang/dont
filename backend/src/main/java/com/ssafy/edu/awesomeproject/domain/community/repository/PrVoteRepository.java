package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.PrVote;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrVoteValue;
import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PrVoteRepository extends JpaRepository<PrVote, Long> {
    interface PrVoteCountProjection {
        Long getPostId();

        Long getTotalVoteCount();
    }

    boolean existsByPostIdAndUserId(Long postId, Long userId);

    long countByPostId(Long postId);

    long countByPostIdAndVoteValue(Long postId, PrVoteValue voteValue);

    @Query(
            """
            select
                v.postId as postId,
                count(v.id) as totalVoteCount
            from PrVote v
            where v.postId in :postIds
            group by v.postId
            """)
    List<PrVoteCountProjection> aggregateByPostIds(@Param("postIds") Collection<Long> postIds);
}
