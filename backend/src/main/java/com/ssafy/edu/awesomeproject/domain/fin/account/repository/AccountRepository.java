package com.ssafy.edu.awesomeproject.domain.fin.account.repository;

import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountRepository extends JpaRepository<Account, Long> {

    Optional<Account> findByAccountNo(String accountNo);

    List<Account> findAllByUserId(Long userId);
}
