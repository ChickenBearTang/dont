package com.ssafy.edu.awesomeproject.domain.fin;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserRole;
import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import jakarta.persistence.EntityManager;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.springframework.jdbc.core.JdbcTemplate;

/** 금융 테스트가 쓰는 사용자·기수 생성 도우미. Cohort 에는 공개 생성자가 없어서 SQL 로 넣는다. */
public final class FinFixtures {

    private FinFixtures() {}

    public static Cohort cohort(JdbcTemplate jdbc, EntityManager em, int generationNo) {
        jdbc.update(
                "insert into cohorts (cohort_code, generation_no, start_date, end_date, created_at, updated_at)"
                        + " values (?, ?, ?, ?, current_timestamp, current_timestamp)",
                "C" + generationNo,
                generationNo,
                LocalDate.of(2026, 1, 1),
                LocalDate.of(2026, 12, 31));
        Long id =
                jdbc.queryForObject(
                        "select id from cohorts where generation_no = ?", Long.class, generationNo);
        return em.find(Cohort.class, id);
    }

    public static User user(EntityManager em, Cohort cohort, String email) {
        User user =
                new User(
                        email,
                        "{noop}pw",
                        "테스터",
                        LocalDate.of(1998, 1, 1),
                        email.substring(0, email.indexOf('@')),
                        null,
                        true,
                        LocalDateTime.now(),
                        UserRole.USER,
                        cohort);
        em.persist(user);
        em.flush();
        return user;
    }
}
