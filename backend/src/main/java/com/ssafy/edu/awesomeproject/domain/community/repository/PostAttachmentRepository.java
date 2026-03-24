package com.ssafy.edu.awesomeproject.domain.community.repository;

import com.ssafy.edu.awesomeproject.domain.community.entity.PostAttachment;
import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PostAttachmentRepository extends JpaRepository<PostAttachment, Long> {

    List<PostAttachment> findAllByPost_IdOrderByDisplayOrderAscIdAsc(Long postId);

    List<PostAttachment> findAllByPost_IdInOrderByPost_IdAscDisplayOrderAscIdAsc(Collection<Long> postIds);

    @Modifying
    @Query("delete from PostAttachment pa where pa.post.id = :postId")
    void deleteByPostId(@Param("postId") Long postId);

    @Query(
            "select pa.post.id as postId, count(pa.id) as attachmentCount "
                    + "from PostAttachment pa "
                    + "where pa.post.id in :postIds "
                    + "group by pa.post.id")
    List<PostAttachmentCountProjection> countByPostIds(@Param("postIds") Collection<Long> postIds);

    interface PostAttachmentCountProjection {
        Long getPostId();

        Long getAttachmentCount();
    }
}
