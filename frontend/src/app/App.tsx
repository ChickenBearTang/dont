import { StrictMode, useEffect, useRef } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import { refreshAccessToken } from '@/features/auth/api/authApi';
import { getErrorStatusCode, isSessionExpiredStatus } from '@/shared/auth/authErrorPolicy';
import { handleSessionExpired } from '@/shared/auth/handleSessionExpired';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { loadAuthUser } from '@/features/auth/utils/authStorage';
import { fetchMyPage } from '@/features/user/api/userApi';
import type { UserProfile } from '@/features/auth/types';
import { queryClient } from '@/shared/api/queryClient';
import { QueryClientProvider } from '@tanstack/react-query';
import '@/styles/index.css';

const AppBootstrap = () => {
  const hasBootstrappedRef = useRef(false);

  const setAuthInitializing = useAuthStore((state) => state.setAuthInitializing);
  const restoreSession = useAuthStore((state) => state.restoreSession);

  useEffect(() => {
    if (hasBootstrappedRef.current) {
      return;
    }

    hasBootstrappedRef.current = true;

    const bootstrapAuth = async () => {
      const savedUser = loadAuthUser();
      setAuthInitializing(true);

      try {
        const response = await refreshAccessToken();
        const nextToken = response.data.accessToken;
        let userForSession = savedUser;

        if (!userForSession) {
          const myPageResponse = await fetchMyPage();
          const myPage = myPageResponse.data;
          userForSession = {
            userId: myPage.userId,
            email: myPage.email,
            nickname: myPage.nickname ?? undefined,
            profileImageUrl: myPage.profileImageUrl ?? undefined,
            onboardingCompleted: myPage.onboardingStatus === 'COMPLETED',
            cohortId: myPage.cohortId ?? undefined,
            role: 'USER',
          } satisfies UserProfile;
        }

        restoreSession({
          accessToken: nextToken,
          user: userForSession,
        });
      } catch (error) {
        const statusCode = getErrorStatusCode(error);
        if (isSessionExpiredStatus(statusCode) && savedUser) {
          handleSessionExpired();
          return;
        }

        console.error('Failed to refresh access token during bootstrap:', error);
      } finally {
        setAuthInitializing(false);
      }
    };

    void bootstrapAuth();
  }, [restoreSession, setAuthInitializing]);

  return (
    <>
      <ToastContainer />
      <RouterProvider router={router} />
    </>
  );
};

export function App() {
  return (
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <AppBootstrap />
        {}
      </QueryClientProvider>
    </StrictMode>
  );
}
