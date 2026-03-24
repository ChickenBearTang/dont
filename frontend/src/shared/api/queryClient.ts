import { QueryClient } from '@tanstack/react-query';

/**
 * 전역 QueryClient 인스턴스
 * 로그아웃 시 캐시를 완전히 비우기 위해 별도 모듈로 분리함
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5분
    },
  },
});
