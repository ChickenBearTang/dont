import { useMutation, useQueryClient } from '@tanstack/react-query';
import { accountApi } from '../api/accountApi';
import { accountKeys } from '../queries/accountKeys';

export const useCreateSaveBox = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.createSaveBox,
    onSuccess: () => {
      // 계좌 목록 정보 무효화
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
};

export const useRefreshAccounts = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.refreshAccounts,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
};

export const useSetPrimaryAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: number) => accountApi.setPrimaryAccount(accountId),
    onSuccess: () => {
      // 전체 계좌 상태가 변할 수 있으므로 all 무효화
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
    mutationFn: (amount: number) => accountApi.executeManualSavings(amount),
    onSuccess: () => {
      // 잔액 변동이 있으므로 전체 무효화
      queryClient.invalidateQueries({ queryKey: accountKeys.all });
    },
  });
};
