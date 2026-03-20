export type AccountStatus = 'ACTIVE' | 'INACTIVE' | 'CLOSED';

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

export interface SavingsSetting {
  id?: number;
  primaryAccountId: number;
  saveBoxAccountId: number;
  keyword: string;
  savingAmount: number;
  isActive: boolean;
}

export interface SaveBoxCreateRequest {
  accountName: string;
}

export interface SavingsSettingRequest {
  primaryAccountId: number;
  saveBoxAccountId: number;
  keyword: string;
  savingAmount: number;
}

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
