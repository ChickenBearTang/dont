package com.ssafy.edu.awesomeproject.domain.community.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(name = "boards")
@Getter
@Entity
@NoArgsConstructor(access = lombok.AccessLevel.PROTECTED)
public class Board extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "category", nullable = false, unique = true, length = 50)
    private String category;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    //TODO: cohert 엔티티 만들면 FK 형식으로 교체 예정
    @Column(name = "cohort_id")
    private Long cohortId;

    public Board(String category, String name, Long cohortId) {
        this.category = category;
        this.name = name;
        this.cohortId = cohortId;
    }
}
