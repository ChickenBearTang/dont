import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { EventSourcePolyfill } from 'event-source-polyfill';

// --- (도메인 타입 힌트 예시) ---
export interface RankingUser {
  userId: number;
  nickname?: string;
  score: number;
  rank: number;
}

export interface RankingListResponse {
  top10: RankingUser[];
  myRanking: RankingUser;
}

export interface RankingResponse {
  status: string;
  message: string;
  data: RankingListResponse;
}

export interface RankingUpdatePayload {
  triggeredUserId: number;
  updatedData?: RankingListResponse;
}

/**
 * 실시간 랭킹 SSE 구독 및 서버 무과부하 렌더링을 관장하는 커스텀 훅
 */
export const useRankingSse = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    // 1. 단방향 스트림 연결 (JWT 헤더 인증 지원)
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';
    const token = useAuthStore.getState().accessToken;

    // axiosInstance가 바라보는 동일한 API BaseURL을 사용하여 404/500 혼합 에러 방지
    const streamUrl = `${API_BASE_URL}/ranking/stream`;

    // 백엔드 Spring Security 필터를 완벽하게 통과하기 위해 헤더 주입이 가능한 Polyfill 객체 사용
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const eventSource = new (EventSourcePolyfill as any)(streamUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    // 2. Nginx 502 방어용 초기 연결 더미 이벤트 수신
    eventSource.addEventListener('connect', (event: Event) => {
      console.log('✅ SSE Pipeline Connected:', (event as MessageEvent).data);
    });

    // 3. 랭킹 변동 알림 수신 (🔥핵심: Thundering Herd 방어🔥)
    eventSource.addEventListener('ranking-update', (event: Event) => {
      // 서버에서 날아온 데이터 파싱
      const payload: RankingUpdatePayload = JSON.parse((event as MessageEvent).data);
      console.log('🔥 실시간 랭킹 변동 감지!', payload);

      // 🚨 [절대 금지 구역] 🚨
      // queryClient.invalidateQueries({ queryKey: ['totalRanking'] });
      // 1만 명이 접속 중일 때 위 로직이 실행되면, 1만 대의 폰에서 동시에 GET /api/ranking API가 호출됩니다.
      // D-DoS 공격과 동일한 부하가 발생하여 단일 EC2 서버는 즉시 사망(OOM/Connection Timeout)합니다.

      // 🛡️ [무과부하 렌더링 - Optimistic Cache Update 방식] 🛡️
      // 방금 만든 RankingPage의 useQuery Key인 ['ranking', 'total'] 과 맞추어 캐시를 덮어씌웁니다.
      // 시니어 피드백 반영: 제네릭 타입 <RankingResponse> 지정으로 ESLint (no-explicit-any) 완벽 방어!
      queryClient.setQueryData<RankingResponse>(['ranking', 'total'], (oldData) => {
        if (!oldData) return oldData; // 화면을 아직 안 보고 있으면 캐싱 안 함

        /* --- [케이스 B] 백엔드에서 이미 랭킹 전체 구조를 통째로 던져준 경우 --- */
        if (payload.updatedData) {
          return {
            ...oldData,
            data: payload.updatedData, // 통째로 갈아끼움!
          };
        }

        return oldData;
      });

      // 💡 [Zustand 연동 시 팁] 💡
      // 만약 랭킹 순위가 아니라 UI 이펙트(빨간 불 깜빡임 등)를 줘야 한다면,
      // useRankingStore.getState().triggerUpdateBlink(); 처럼
      // Zustand 액션을 호출하여 전역 화면에 알림 배지만 살짝 띄우는 용도로도 응용 가능합니다.
    });

    // 네트워크 끊김이나 타임아웃 처리
    eventSource.addEventListener('error', (error: Event) => {
      console.error('❌ SSE Connection Error. Retrying...', error);
      // EventSource는 자동으로 재연결(Reconnect)을 시도하므로 별도 로직 없이 두어도 되지만,
      // 무한 루프 에러를 막기 위해 일시적으로 close() 할 수도 있습니다.
    });

    // 4. 컴포넌트 마운트 해제 시 소켓이 둥둥 떠다니는 메모리 릭(Leak) 완벽 차단
    return () => {
      console.info('🧹 Cleaning up SSE Connection');
      eventSource.close();
    };
  }, [queryClient]);
};
