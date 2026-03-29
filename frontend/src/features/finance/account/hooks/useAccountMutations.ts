import { useMutation, useQueryClient } from '@tanstack/react-query';
import { accountApi } from '../api/accountApi';
import { accountKeys } from '../queries/accountKeys';

/**
 * 신규 세이브박스 개설 mutation 훅
 */
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

/**
 * 계좌 목록 새로고침(동기화) mutation 훅
 */
export const useRefreshAccounts = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.refreshAccounts,
    onSuccess: () => {
      // 모든 계좌 정보(목록, 상세, 설정 등)를 무효화하여 한 번에 정합성 확보
      queryClient.invalidateQueries({ queryKey: accountKeys.all });
    },
  });
};

/**
 * 주계좌 설정 mutation 훅
 */
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

/**
 * 자동 저축 설정 저장 mutation 훅
 */
export const useSaveSavingsSetting = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.saveSavingsSetting,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.savings() });
    },
  });
};

/**
 * 수동 저축 실행 mutation 훅
 */
export const useExecuteManualSavings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ amount, password }: { amount: number; password: string }) =>
      accountApi.executeManualSavings(amount, password),
    onSuccess: () => {
      // 잔액 변동이 있으므로 전체 무효화
      queryClient.invalidateQueries({ queryKey: accountKeys.all });
    },
  });
};

/**
 * 금융 계좌 연동 mutation 훅
 */
export const useLinkFinanceAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountApi.linkFinanceAccount,
    onSuccess: () => {
      // 연동 성공 시 전체 계좌 정보를 무효화하여 새로 불러옴
      queryClient.invalidateQueries({ queryKey: accountKeys.all });
    },
  });
};
