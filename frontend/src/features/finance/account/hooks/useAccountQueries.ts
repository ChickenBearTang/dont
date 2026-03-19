import { useQuery } from '@tanstack/react-query';
import { accountApi } from '../api/accountApi';
import { accountKeys } from '../queries/accountKeys';

/**
 * 사용자의 전체 계좌 목록 조회 훅
 */
export const useGetMyAccounts = () => {
  return useQuery({
    queryKey: accountKeys.lists(),
    queryFn: accountApi.getMyAccounts,
    select: (response) => response.data.accounts,
  });
};

/**
 * 특정 계좌 상세 정보 조회 훅
 */
export const useGetAccountDetail = (accountId: number) => {
  return useQuery({
    queryKey: accountKeys.detail(accountId),
    queryFn: () => accountApi.getAccountDetail(accountId),
    select: (response) => response.data,
    enabled: !!accountId,
  });
};

/**
 * 특정 계좌 거래 내역 조회 훅
 */
export const useGetAccountTransactions = (
  accountId: number,
  params: { startDate: string; endDate: string }
) => {
  return useQuery({
    queryKey: accountKeys.transactions(accountId, params),
    queryFn: () => accountApi.getAccountTransactions(accountId, params),
    select: (response) => response.data.transactions,
    enabled: !!accountId,
  });
};

/**
 * 현재 저축 설정 조회 훅
 */
export const useGetSavingsSetting = () => {
  return useQuery({
    queryKey: accountKeys.savings(),
    queryFn: accountApi.getSavingsSetting,
    select: (response) => response.data,
  });
};
