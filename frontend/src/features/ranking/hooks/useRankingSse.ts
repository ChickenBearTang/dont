import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { refreshAccessToken } from '@/features/auth/api/authApi';
import { getErrorStatusCode, isSessionExpiredStatus } from '@/shared/auth/authErrorPolicy';
import { handleSessionExpired } from '@/shared/auth/handleSessionExpired';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useRankingStore } from '../store/useRankingStore';

const REFRESH_COOLDOWN_MS = 10000;

export interface RankingUser {
  userId: number;
  nickname?: string;
  score: number;
  rank: number;
  cohortNo?: number;
  profileImageUrl?: string;
  rankDiff?: number | null;
}

export interface RankingListResponse {
  top100: RankingUser[];
  myRanking: RankingUser;
}

export interface RankingResponse {
  status: string;
  message: string;
  data: RankingListResponse;
}

export interface RankingUpdatePayload {
  triggeredUserId: number;
  totalTop100: RankingUser[];
  cohortNo?: number;
  cohortTop100?: RankingUser[];
}

export const useRankingSse = () => {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
  const setIsUpdating = useRankingStore((state) => state.setIsUpdating);

  const queryClientRef = useRef(queryClient);
  const setIsUpdatingRef = useRef(setIsUpdating);
  const setAccessTokenRef = useRef(setAccessToken);
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastTokenRef = useRef<string | null>(null);

  useEffect(() => {
    queryClientRef.current = queryClient;
    setIsUpdatingRef.current = setIsUpdating;
    setAccessTokenRef.current = setAccessToken;
  }, [queryClient, setIsUpdating, setAccessToken]);

  useEffect(() => {
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

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';
    const streamUrl = `${apiBaseUrl}/ranking/stream`;

    lastTokenRef.current = token;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    let refreshInFlight = false;
    let lastRefreshAt = 0;

    const eventSource = new EventSourcePolyfill(streamUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      withCredentials: true,
      heartbeatTimeout: 60000,
    });

    eventSourceRef.current = eventSource as unknown as EventSource;

    eventSource.addEventListener('ranking-update', (event) => {
      try {
        const payload: RankingUpdatePayload = JSON.parse((event as MessageEvent<string>).data);
        const qClient = queryClientRef.current;

        if (payload.totalTop100) {
          const newTop100 = payload.totalTop100;
          qClient.setQueryData<RankingResponse>(['ranking', 'total'], (oldData: RankingResponse | undefined) => {
            if (!oldData) return oldData;
            return {
              ...oldData,
              status: 'success',
              data: {
                ...oldData.data,
                top100: newTop100
              }
            };
          });
        }

        if (payload.cohortNo && payload.cohortTop100) {
          const newCohortTop100 = payload.cohortTop100;
          qClient.setQueryData<RankingResponse>(
            ['ranking', 'cohort', payload.cohortNo],
            (oldData: RankingResponse | undefined) => {
              if (!oldData) return oldData;
              return {
                ...oldData,
                status: 'success',
                data: {
                  ...oldData.data,
                  top100: newCohortTop100
                }
              };
            }
          );
        }

        setIsUpdatingRef.current(true);
        setTimeout(() => {
          qClient.invalidateQueries({ queryKey: ['ranking'] }).finally(() => {
            setIsUpdatingRef.current(false);
          });
        }, 1000 + Math.random() * 1000);
      } catch (err) {
        console.error('Ranking SSE payload parse error:', err);
      }
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
        setAccessTokenRef.current(nextToken);
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
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      lastTokenRef.current = null;
    };
  }, [token]);
};
