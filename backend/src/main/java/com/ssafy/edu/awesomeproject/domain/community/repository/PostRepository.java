package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import com.ssafy.edu.awesomeproject.domain.community.entity.Post;
import com.ssafy.edu.awesomeproject.domain.community.entity.PostStatus;
import java.util.Collection;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;


public interface PostRepository extends JpaRepository<Post, Long> {
    Optional<Post> findByIdAndStatus(Long id, PostStatus status);

    Optional<Post> findByIdAndStatusIn(Long id, Collection<PostStatus> statuses);

    Page<Post> findByStatus(PostStatus status, Pageable pageable);

    Page<Post> findByStatusIn(Collection<PostStatus> statuses, Pageable pageable);

    Page<Post> findByBoard_CategoryAndStatus(
            BoardCategory category, PostStatus status, Pageable pageable);

    Page<Post> findByBoard_CategoryAndStatusIn(
            BoardCategory category, Collection<PostStatus> statuses, Pageable pageable);


    Page<Post> findByBoard_CategoryAndBoard_Cohort_GenerationNoAndStatus(
            BoardCategory category, Integer generationNo, PostStatus status, Pageable pageable);

    Page<Post> findByBoard_CategoryAndBoard_Cohort_GenerationNoAndStatusIn(
            BoardCategory category,
            Integer generationNo,
            Collection<PostStatus> statuses,
            Pageable pageable);

    @Query(
            """
    select p
    from Post p
    join p.board b
    left join b.cohort c
    where p.status in :statuses
      and (
            b.category <> :cohortCategory
            or c.generationNo = :generationNo
          )
    """)
    Page<Post> findVisiblePostsForUser(
            @Param("statuses") Collection<PostStatus> statuses,
            @Param("cohortCategory") BoardCategory cohortCategory,
            @Param("generationNo") Integer generationNo,
            Pageable pageable);
}
