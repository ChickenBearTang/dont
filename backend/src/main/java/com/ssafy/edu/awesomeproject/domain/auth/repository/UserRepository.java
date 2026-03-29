package com.ssafy.edu.awesomeproject.domain.auth.repository;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserStatus;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {
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
    boolean existsBySsafyFinanceUserKey(String ssafyFinanceUserKey);

    List<User> findByCohortId(Long cohortId);

    List<User> findAllByStatus(UserStatus status);
}
