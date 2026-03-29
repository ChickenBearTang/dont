import { useMutation, useQueryClient } from '@tanstack/react-query';
import { accountApi } from '../api/accountApi';
import { accountKeys } from '../queries/accountKeys';


export const useCreateSaveBox = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.createSaveBox,
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ['ranking'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'ranking'] });
    },
  });
};


export const useRefreshAccounts = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.refreshAccounts,
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: accountKeys.all });
    },
  });
};


export const useSetPrimaryAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: number) => accountApi.setPrimaryAccount(accountId),
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: accountKeys.all });
    },
  });
};


export const useSaveSavingsSetting = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.saveSavingsSetting,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.savings() });
    },
  });
};


export const useExecuteManualSavings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ amount, password }: { amount: number; password: string }) =>
      accountApi.executeManualSavings(amount, password),
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: accountKeys.all });
      queryClient.invalidateQueries({ queryKey: ['ranking'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'ranking'] });
    },
  });
};


export const useExecuteManualWithdrawal = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ amount, password }: { amount: number; password: string }) =>
      accountApi.executeManualWithdrawal(amount, password),
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: accountKeys.all });
      queryClient.invalidateQueries({ queryKey: ['ranking'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'ranking'] });
    },
  });
};


export const useLinkFinanceAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.linkFinanceAccount,
    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: accountKeys.all });
    },
  });
};
