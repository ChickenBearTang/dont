


export interface ApiResponse<T = unknown> {
  success: boolean;
  code: string;
  message: string;
  data: T;
}


export interface SelectOption {
  value: string | number;
  label: string;
}

export interface Cohort {
  cohortId: number;
  cohortCode: string;
  generationNo: number;
}
