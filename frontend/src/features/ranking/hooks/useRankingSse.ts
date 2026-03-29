import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useRankingStore } from '../store/useRankingStore';
import { EventSourcePolyfill } from 'event-source-polyfill';

// --- (도메인 타입 힌트 예시) ---
export interface RankingUser {
  userId: number;
  nickname?: string;
  score: number;
  rank: number;
  cohortNo?: number;
  profileImageUrl?: string;
  rankDiff?: number;
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
  totalTop10: RankingUser[];
  cohortNo?: number;
  cohortTop10?: RankingUser[];
}

/**
 * 실시간 랭킹 SSE 구독 및 서버 무과부하 렌더링을 관장하는 커스텀 훅
 */
export const useRankingSse = () => {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const setIsUpdating = useRankingStore((state) => state.setIsUpdating);

  // 최신 값들을 참조하기 위한 REF (의존성 배열에서 제외하여 리렌더링 방지)
  const queryClientRef = useRef(queryClient);
  const setIsUpdatingRef = useRef(setIsUpdating);
  const eventSourceRef = useRef<any>(null);
  const lastTokenRef = useRef<string | null>(null);

  useEffect(() => {
    queryClientRef.current = queryClient;
    setIsUpdatingRef.current = setIsUpdating;
  }, [queryClient, setIsUpdating]);

  useEffect(() => {
    // 토큰이 없거나, 이전과 같은 토큰이면 연결을 유지 (불필요한 재연결 방지)
    if (!token) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    if (lastTokenRef.current === token && eventSourceRef.current) {
      return;
    }

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';
    const streamUrl = `${API_BASE_URL}/ranking/stream`;

    console.info('📡 [SSE] Creating new stable connection...');
    lastTokenRef.current = token;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new (EventSourcePolyfill as any)(streamUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      withCredentials: true,
      heartbeatTimeout: 60000,
    });

    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.info('✅ [SSE] Server-sent events connected.');
    };

    eventSource.addEventListener('connect', (event: Event) => {
      console.log('🚀 [SSE Debug] Pipeline active:', (event as MessageEvent).data);
    });

    eventSource.addEventListener('ranking-update', (event: Event) => {
      console.log('📡 [SSE Debug] ranking-update received');
      try {
        const payload: RankingUpdatePayload = JSON.parse((event as MessageEvent).data);
        const qClient = queryClientRef.current;
        
        // 1. 캐시 즉시 업데이트
        qClient.setQueryData<RankingResponse>(['ranking', 'total'], (oldData: RankingResponse | undefined) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            data: { ...oldData.data, top10: payload.totalTop10 }
          };
        });

        if (payload.cohortNo) {
          qClient.setQueryData<RankingResponse>(
            ['ranking', 'cohort', payload.cohortNo],
            (oldData: RankingResponse | undefined) => {
              if (!oldData || !payload.cohortTop10) return oldData;
              return {
                ...oldData,
                data: { ...oldData.data, top10: payload.cohortTop10 }
              };
            }
          );
        }

        // 2. 전체 데이터 보정 (지연 호출로 UI 흔들림 방지)
        setIsUpdatingRef.current(true);
        setTimeout(() => {
          qClient.invalidateQueries({ queryKey: ['ranking'] }).finally(() => {
            setIsUpdatingRef.current(false);
          });
        }, 1000 + Math.random() * 1000);

      } catch (err) {
        console.error('❌ [SSE] Payload error:', err);
      }
    });

    eventSource.onerror = (err: any) => {
      console.error('❌ [SSE] Connection error:', err);
    };

    return () => {
      // 컴포넌트 언마운트 시에만 정리 (토큰 변경 시엔 위에서 별도 처리)
      console.info('🧹 [SSE] Cleaning up on unmount');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      lastTokenRef.current = null;
    };
  }, [token]); // 오직 토큰 값 기반으로만 재작동 여부 결정
};
