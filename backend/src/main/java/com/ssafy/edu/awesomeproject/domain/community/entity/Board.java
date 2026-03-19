package com.ssafy.edu.awesomeproject.domain.community.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
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

    // ENUM 교체
    // cohort 여러 기수 존재할 수 있으므로 unique=true 제거
    @Enumerated(EnumType.STRING)
    @Column(name = "category", nullable = false, length = 50)
    private BoardCategory category;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    // cohort entity 추가로 FK 조건 추가
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cohort_id")
    private Cohort cohort;

    public Board(BoardCategory boardCategory, String name, Cohort cohort) {
        this.category = boardCategory;
        this.name = name;
        this.cohort = cohort;
    }

    public boolean isCohortBoard() {
        return this.category == BoardCategory.COHORT;
    }
}
