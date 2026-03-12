package com.ssafy.edu.awesomeproject.domain.community.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
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

    //ENUM 교체
    //cohort 여러 기수 존재할 수 있으므로 unique=true 제거
    @Enumerated(EnumType.STRING)
    @Column(name = "category", nullable = false, length = 50)
    private BoardCategory category;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Column(name = "cohort_id")
    private Long cohortId;

    public Board(BoardCategory boardCategory, String name, Long cohortId) {
        this.category = boardCategory;
        this.name = name;
        this.cohortId = cohortId;
    }

    public boolean isCohortBoard() {
        return this.category == BoardCategory.COHORT;
    }
}
