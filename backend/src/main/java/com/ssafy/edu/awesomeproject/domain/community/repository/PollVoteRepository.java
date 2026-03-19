package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.PollVote;
import com.ssafy.edu.awesomeproject.domain.community.entity.PollVoteOption;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PollVoteRepository extends JpaRepository<PollVote, Long> {
    interface PollVoteCountProjection {
        Long getPostId();

        Long getOptionACount();

        Long getOptionBCount();

        Long getTotalVoteCount();
    }

    Optional<PollVote> findByPostIdAndUserId(Long postId, Long userId);

    long countByPostId(Long postId);

    long countByPostIdAndVoteOption(Long postId, PollVoteOption voteOption);

    @Query(
            """
            select
                v.postId as postId,
                coalesce(sum(case when v.voteOption = :optionA then 1 else 0 end), 0) as optionACount,
                coalesce(sum(case when v.voteOption = :optionB then 1 else 0 end), 0) as optionBCount,
                count(v.id) as totalVoteCount
            from PollVote v
            where v.postId in :postIds
            group by v.postId
            """)
    List<PollVoteCountProjection> aggregateByPostIdsInternal(
            @Param("postIds") Collection<Long> postIds,
            @Param("optionA") PollVoteOption optionA,
            @Param("optionB") PollVoteOption optionB);

    default List<PollVoteCountProjection> aggregateByPostIds(Collection<Long> postIds) {
        return aggregateByPostIdsInternal(
                postIds, PollVoteOption.OPTION_A, PollVoteOption.OPTION_B);
    }
}
