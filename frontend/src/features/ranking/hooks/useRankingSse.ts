import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// --- (도메인 타입 힌트 예시) ---
export interface RankingUser {
  userId: number;
  score: number;
  rank: number;
}

export interface RankingUpdatePayload {
  triggeredUserId: number;
  // 단일 서버 부하를 극한으로 없애기 위해, 백엔드에서 랭킹 변동 시점의
  // '최신 Top 100 랭킹 리스트' 전체를 payload에 담아 보내주는 방식을 강력 추천합니다.
  updatedTop100?: RankingUser[];
}

/**
 * 실시간 랭킹 SSE 구독 및 서버 무과부하 렌더링을 관장하는 커스텀 훅
 */
export const useRankingSse = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    // 1. 단방향 스트림 연결 (쿠키 기반 인증 시 withCredentials 필수)
    // ※ JWT 헤더 전송이 반드시 필요하다면 EventSourcePolyfill 라이브러리를 사용하세요.
    const eventSource = new EventSource('/api/ranking/stream', {
      withCredentials: true,
    });

    // 2. Nginx 502 방어용 초기 연결 더미 이벤트 수신
    eventSource.addEventListener('connect', (event) => {
      console.log('✅ SSE Pipeline Connected:', (event as MessageEvent).data);
    });

    // 3. 랭킹 변동 알림 수신 (🔥핵심: Thundering Herd 방어🔥)
    eventSource.addEventListener('ranking-update', (event) => {
      // 서버에서 날아온 데이터 파싱
      const payload: RankingUpdatePayload = JSON.parse((event as MessageEvent).data);
      console.log('🔥 실시간 랭킹 변동 감지!', payload);

      // 🚨 [절대 금지 구역] 🚨
      // queryClient.invalidateQueries({ queryKey: ['totalRanking'] });
      // 1만 명이 접속 중일 때 위 로직이 실행되면, 1만 대의 폰에서 동시에 GET /api/ranking API가 호출됩니다.
      // D-DoS 공격과 동일한 부하가 발생하여 단일 EC2 서버는 즉시 사망(OOM/Connection Timeout)합니다.

      // 🛡️ [무과부하 렌더링 - Optimistic Cache Update 방식] 🛡️
      queryClient.setQueryData(['totalRanking'], (oldData: RankingUser[] | undefined) => {
        if (!oldData) return oldData; // 화면을 아직 안 보고 있으면 캐싱 안 함

        /* --- [케이스 A] 변동 대상 유저 ID만 왔을 경우 (수동 계산) --- */
        // return oldData.map(user =>
        //   user.userId === payload.triggeredUserId
        //     ? { ...user, score: user.score + (방금 저축한 금액), rank: (재계산) }
        //     : user
        // ).sort((a, b) => b.score - a.score);

        /* --- [케이스 B] 백엔드에서 이미 최신화된 Top 100 배열을 던져준 경우 (가장 이상적) --- */
        if (payload.updatedTop100) {
          return payload.updatedTop100; // API 폴링 "0"번으로 화면의 숫자가 스르륵 변경됨
        }

        return oldData;
      });

      // 💡 [Zustand 연동 시 팁] 💡
      // 만약 랭킹 순위가 아니라 UI 이펙트(빨간 불 깜빡임 등)를 줘야 한다면,
      // useRankingStore.getState().triggerUpdateBlink(); 처럼
      // Zustand 액션을 호출하여 전역 화면에 알림 배지만 살짝 띄우는 용도로도 응용 가능합니다.
    });

    // 네트워크 끊김이나 타임아웃 처리
    eventSource.addEventListener('error', (error) => {
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
