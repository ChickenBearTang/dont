/**
 * 계좌 도메인 관련 타입 정의
 */

/**
 * 계좌 상태 정보
 */
export type AccountStatus = 'ACTIVE' | 'INACTIVE' | 'CLOSED';

/**
 * 계좌 상세 정보 (목록 조회 시 각 항목)
 */
export interface AccountDetail {
  id: number;
  bankCode: string;
  bankName: string;
  userName: string;
  accountNo: string;
  accountName: string;
  accountTypeCode: string;
  accountTypeName: string;
  accountCreatedDate: string;
  accountExpiryDate: string;
  dailyTransferLimit: string;
  oneTimeTransferLimit: string;
  accountBalance: string;
  lastTransactionDate: string;
  currencyCode: string;
}

/**
 * 계좌 요약 정보 (AccountResponse)
 */
export interface Account {
  id: number;
  bankName: string;
  bankCode: string;
  accountNo: string;
  accountName: string;
  balance: number;
  userName: string;
  status: AccountStatus;
}

/**
 * 계좌 거래 내역 항목
 */
export interface TransactionItem {
  transactionUniqueNo: string;
  transactionDate: string;
  transactionTime: string;
  transactionType: '1' | '2'; // 1: 입금, 2: 출금
  transactionTypeName: string;
  transactionAmount: string;
  afterBalance: string;
  transactionSummary: string;
  transactionMemo: string;
}

/**
 * 저축 설정 정보
 */
export interface SavingsSetting {
  id?: number;
  primaryAccountId: number;
  saveBoxAccountId: number;
  keyword: string;
  savingAmount: number;
  isActive: boolean;
}

/* --- API Requests --- */

export interface SaveBoxCreateRequest {
  accountName: string;
}

export interface SavingsSettingRequest {
  primaryAccountId: number;
  saveBoxAccountId: number;
  keyword: string;
  savingAmount: number;
}

/* --- API Responses --- */

export interface AccountListResponse {
  accounts: AccountDetail[];
}

export interface AccountTransactionResponse {
  accountNo: string;
  accountName: string;
  transactions: TransactionItem[];
}

export interface AccountCreateResponse {
  accountNo: string;
  bankCode: string;
  bankName: string;
}
