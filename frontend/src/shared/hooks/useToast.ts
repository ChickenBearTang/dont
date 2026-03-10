import { useUIStore } from '@/shared/store/useUIStore';

/**
 * 토스트 알림을 더 쉽게 사용하기 위한 훅
 */
export const useToast = () => {
  const addToast = useUIStore((state) => state.addToast);

  return {
    success: (message: string) => addToast(message, 'success'),
    error: (message: string) => addToast(message, 'error'),
    info: (message: string) => addToast(message, 'info'),
  };
};
