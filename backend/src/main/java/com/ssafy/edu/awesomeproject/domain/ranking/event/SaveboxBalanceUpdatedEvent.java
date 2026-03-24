package com.ssafy.edu.awesomeproject.domain.ranking.event;

/** 세이브박스 잔액 변동 완료 후 발생하는 비동기 통신용 내부 이벤트 객체 */
public record SaveboxBalanceUpdatedEvent(Long userId, Long currentBalance, Integer cohort) {}
