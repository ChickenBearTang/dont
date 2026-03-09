// 프로젝트 전체에서 공통으로 사용되는 타입 모음입니다.

/**
 * 백엔드 공통 API 응답 규격
 */
export interface ApiResponse<T = any> {
  success: boolean;
  code: string;
  message: string;
  data: T;
}

/**
 * 전역에서 사용되는 기수(Cohort) 정보
 */
export interface SelectOption {
  value: string | number;
  label: string;
}

export interface Cohort {
  cohortId: number;
  cohortCode: string;
}
