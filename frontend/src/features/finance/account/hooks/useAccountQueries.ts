import { useQuery } from '@tanstack/react-query';
import { accountApi } from '../api/accountApi';
import { accountKeys } from '../queries/accountKeys';


export const useGetMyAccounts = () => {
  return useQuery({
    queryKey: accountKeys.lists(),
    queryFn: accountApi.getMyAccounts,
    select: (response) => {
      const sortedAccounts = [...response.data.accounts].sort((a, b) => {
        const balanceA = Number(a.accountBalance) || 0;
        const balanceB = Number(b.accountBalance) || 0;
        return balanceB - balanceA;
      });
      return sortedAccounts;
    },
  });
};


export const useGetAccountDetail = (accountId: number) => {
  return useQuery({
    queryKey: accountKeys.detail(accountId),
    queryFn: () => accountApi.getAccountDetail(accountId),
    select: (response) => response.data,
    enabled: !!accountId,
  });
};


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


export const useGetSavingsSetting = () => {
  return useQuery({
    queryKey: accountKeys.savings(),
    queryFn: accountApi.getSavingsSetting,
    select: (response) => response.data,
  });
};
