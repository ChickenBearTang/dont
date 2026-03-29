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


export const accountApi = {


  getMyAccounts: (): Promise<ApiResponse<AccountListResponse>> => {
    return axiosInstance.get('/fin/accounts');
  },


  getAccountDetail: (accountId: number): Promise<ApiResponse<Account>> => {
    return axiosInstance.get(`/fin/accounts/${accountId}`);
  },


  createSaveBox: (data: SaveBoxCreateRequest): Promise<ApiResponse<AccountCreateResponse>> => {
    return axiosInstance.post('/fin/accounts/save-box', data);
  },


  refreshAccounts: (): Promise<ApiResponse<AccountListResponse>> => {
    return axiosInstance.post('/fin/accounts/refresh');
  },


  setPrimaryAccount: (accountId: number): Promise<ApiResponse<Account>> => {
    return axiosInstance.patch(`/fin/accounts/${accountId}/primary`);
  },


  getAccountTransactions: (
    accountId: number,
    params: { startDate: string; endDate: string }
  ): Promise<ApiResponse<AccountTransactionResponse>> => {
    return axiosInstance.get(`/fin/accounts/${accountId}/transactions`, {
      params,
    });
  },


  getSavingsSetting: (): Promise<ApiResponse<SavingsSetting>> => {
    return axiosInstance.get('/fin/accounts/savings-settings');
  },


  saveSavingsSetting: (data: SavingsSettingRequest): Promise<ApiResponse<SavingsSetting>> => {
    return axiosInstance.post('/fin/accounts/savings-settings', data);
  },


  executeManualSavings: (amount: number, password: string): Promise<ApiResponse<void>> => {
    return axiosInstance.post('/fin/accounts/manual-savings', { amount, password });
  },


  executeManualWithdrawal: (amount: number, password: string): Promise<ApiResponse<void>> => {
    return axiosInstance.post('/fin/accounts/manual-withdrawal', { amount, password });
  },


  linkFinanceAccount: (userKey: string): Promise<ApiResponse<AccountListResponse>> => {
    return axiosInstance.post('/fin/accounts/link', null, {
      params: { userKey },
    });
  },
};
