import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  Account,
  AccountListResponse,
  AccountTransactionResponse,
  SaveBoxCreateRequest,
  SavingsSetting,
  SavingsSettingRequest,
  AccountCreateResponse,
} from '../types';

/**
 * 계좌 관리 API 서비스
 */
export const accountApi = {
  /**
   * 사용자의 수시입출금 계좌 목록을 조회합니다.
   */
  getMyAccounts: (): Promise<ApiResponse<AccountListResponse>> => {
    return axiosInstance.get('/fin/accounts');
  },

  /**
   * 특정 계좌의 상세 정보를 조회합니다.
   */
  getAccountDetail: (accountId: number): Promise<ApiResponse<Account>> => {
    return axiosInstance.get(`/fin/accounts/${accountId}`);
  },

  /**
   * 신규 '세이브 박스' 계좌를 개설합니다.
   */
  createSaveBox: (data: SaveBoxCreateRequest): Promise<ApiResponse<AccountCreateResponse>> => {
    return axiosInstance.post('/fin/accounts/save-box', data);
  },

  /**
   * 외부 API 기반으로 계좌 정보를 재동기화합니다.
   */
  refreshAccounts: (): Promise<ApiResponse<AccountListResponse>> => {
    return axiosInstance.post('/fin/accounts/refresh');
  },

  /**
   * 특정 계좌를 '주 계좌'로 설정합니다.
   */
  setPrimaryAccount: (accountId: number): Promise<ApiResponse<Account>> => {
    return axiosInstance.patch(`/fin/accounts/${accountId}/primary`);
  },

  /**
   * 특정 계좌의 거래 내역을 조회합니다.
   */
  getAccountTransactions: (
    accountId: number,
    params: { startDate: string; endDate: string }
  ): Promise<ApiResponse<AccountTransactionResponse>> => {
    return axiosInstance.get(`/fin/accounts/${accountId}/transactions`, {
      params,
    });
  },

  /**
   * 사용자의 현재 자동 저축 설정을 조회합니다.
   */
  getSavingsSetting: (): Promise<ApiResponse<SavingsSetting>> => {
    return axiosInstance.get('/fin/accounts/savings-settings');
  },

  /**
   * 자동 저축 규칙을 설정(생성/수정)합니다.
   */
  saveSavingsSetting: (data: SavingsSettingRequest): Promise<ApiResponse<SavingsSetting>> => {
    return axiosInstance.post('/fin/accounts/savings-settings', data);
  },

  /**
   * 주계좌에서 세이브박스로 직접 금액을 이체합니다.
   */
  executeManualSavings: (amount: number): Promise<ApiResponse<void>> => {
    return axiosInstance.post('/fin/accounts/manual-savings', null, {
      params: { amount },
    });
  },
};
