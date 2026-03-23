# Project Scope And Current Plan

## 목표

이 프로젝트의 목표는 다음과 같다.

- 금융 서비스 소비 리포트 POC 구현
- 원천 금융 데이터 기반 통계 생성
- 이상 거래 탐지
- Gemini 기반 AI 해설 생성
- 프론트에서 시각화 가능한 월간 소비 화면 제공

## 현재 완료 상태

### 데이터

- 사용자 8명, 6개월 raw 데이터 구축 완료
- 카드/계좌 정합성 맞춤 완료

### 백엔드

- FastAPI 엔드포인트 구성 완료
- 종합 소비 리포트 API 완료
- 월간 목업 통계 API 완료
- generated 산출물 재생성 스크립트 완료

### AI

- Gemini 연동 완료
- fallback analysis 완료
- 프론트 하단 AI 분석 섹션 연결 완료

### 프론트

- 월간 소비 목업 화면 구현 완료
- 회원/월 선택 완료
- 월 누적선/6개월 평균/카테고리 분석 시각화 완료

## 현재 아키텍처 방향

### 유지하는 부분

- 숫자 계산은 코드가 담당
- AI는 해설 담당
- generated는 raw에서 재생성 가능해야 함

### 확장 가능한 부분

- representative raw samples를 LLM 입력에 추가
- merchant-level insight 추가
- 카테고리 재분류 고도화
- 사용자별 generated manifest 구조 추가 정리

## 남은 개선 여지

- 문서와 프론트 용어 통일
- generated root 파일 구조 개선
- AI 입력 payload 확장
- 프론트에서 월 선택 시 AI 분석 범위를 더 명확히 표시
