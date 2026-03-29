package com.ssafy.edu.awesomeproject.domain.ranking.event;


public record SaveboxBalanceUpdatedEvent(Long userId, Long currentBalance, Integer cohort) {}
