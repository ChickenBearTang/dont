package com.ssafy.edu.awesomeproject.domain.auth.repository;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserStatus;

import java.util.List;
import java.util.Optional;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface UserRepository extends JpaRepository<User, Long> {

    /** 사용자별로 순서를 맞춰야 하는 작업(계좌 개설 등)이 쓰는 행 잠금 조회. */
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select u from User u where u.id = :id")
    Optional<User> findByIdForUpdate(@Param("id") Long id);

    Optional<User> findByEmail(String email);

    Optional<User> findByEmailAndStatus(String email, UserStatus status);

    Optional<User> findByIdAndStatus(Long id, UserStatus status);

    boolean existsByEmail(String email);

    boolean existsByIdAndStatus(Long id, UserStatus status);

    boolean existsByNickname(String nickname);

    boolean existsByNicknameAndIdNot(String nickname, Long id);

    default Optional<User> findActiveByEmail(String email) {
        return findByEmailAndStatus(email, UserStatus.ACTIVE);
    }

    default Optional<User> findActiveById(Long id) {
        return findByIdAndStatus(id, UserStatus.ACTIVE);
    }

    default boolean existsActiveById(Long id) {
        return existsByIdAndStatus(id, UserStatus.ACTIVE);
    }

    List<User> findByCohortId(Long cohortId);

    List<User> findAllByStatus(UserStatus status);
}
