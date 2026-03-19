package com.ssafy.edu.awesomeproject.domain.auth.repository;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);
}
