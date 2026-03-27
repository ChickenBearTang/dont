import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { refreshAccessToken } from '@/features/auth/api/authApi';
import { getErrorStatusCode, isSessionExpiredStatus } from '@/shared/auth/authErrorPolicy';
import { handleSessionExpired } from '@/shared/auth/handleSessionExpired';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

const REFRESH_COOLDOWN_MS = 10000;

export interface RankingUser {
  userId: number;
  nickname?: string;
  score: number;
  rank: number;
  cohortNo?: number;
  profileImageUrl?: string;
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

export const useRankingSse = () => {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const setAccessToken = useAuthStore((state) => state.setAccessToken);

  useEffect(() => {
    if (!token) {
      return;
    }

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';
    const streamUrl = `${apiBaseUrl}/ranking/stream`;

    let refreshInFlight = false;
    let lastRefreshAt = 0;

    const eventSource = new (EventSourcePolyfill as any)(streamUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      withCredentials: true,
    });

    eventSource.addEventListener('connect', (event: Event) => {
      console.log('Ranking SSE connected:', (event as MessageEvent).data);
    });

    eventSource.addEventListener('ranking-update', (event: Event) => {
      const payload: RankingUpdatePayload = JSON.parse((event as MessageEvent).data);

      queryClient.setQueryData<RankingResponse>(['ranking', 'total'], (oldData) => {
        if (!oldData) {
          return oldData;
        }

        if (payload.updatedData) {
          return {
            ...oldData,
            data: payload.updatedData,
          };
        }

        return oldData;
      });
    });

    eventSource.addEventListener('error', async () => {
      const now = Date.now();

      if (refreshInFlight || now - lastRefreshAt < REFRESH_COOLDOWN_MS) {
        return;
      }

      refreshInFlight = true;
      lastRefreshAt = now;

      try {
        const response = await refreshAccessToken();
        const nextToken = response.data.accessToken;
        setAccessToken(nextToken);
        eventSource.close();
      } catch (error) {
        const statusCode = getErrorStatusCode(error);
        if (isSessionExpiredStatus(statusCode)) {
          handleSessionExpired();
          eventSource.close();
          return;
        }

        console.warn('Ranking SSE token refresh skipped due to non-auth error:', error);
      } finally {
        refreshInFlight = false;
      }
    });

    return () => {
      eventSource.close();
    };
  }, [queryClient, setAccessToken, token]);
};
