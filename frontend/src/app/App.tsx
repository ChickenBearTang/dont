import { StrictMode, useEffect, useRef } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import { refreshAccessToken } from '@/features/auth/api/authApi';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { loadAuthUser } from '@/features/auth/utils/authStorage';
import { queryClient } from '@/shared/api/queryClient';
import { QueryClientProvider } from '@tanstack/react-query';
import '@/styles/index.css';

const AppBootstrap = () => {
  const hasBootstrappedRef = useRef(false);

  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const setAuthInitializing = useAuthStore((state) => state.setAuthInitializing);
  const restoreSession = useAuthStore((state) => state.restoreSession);
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    if (hasBootstrappedRef.current) {
      return;
    }

    hasBootstrappedRef.current = true;

    const bootstrapAuth = async () => {
      setAuthInitializing(true);

      try {
        const response = await refreshAccessToken();
        const nextToken = response.data.accessToken;
        const savedUser = loadAuthUser();

        restoreSession({
          accessToken: nextToken,
          user: savedUser,
        });
      } catch (error) {
        const statusCode =
          typeof error === 'object' && error !== null && 'response' in error
            ? (error as { response?: { status?: number } }).response?.status
            : undefined;

        if (statusCode === 401 || statusCode === 403) {
          logout();
          return;
        }

        console.error('Failed to refresh access token during bootstrap:', error);
      } finally {
        setAuthInitializing(false);
      }
    };

    void bootstrapAuth();
  }, [logout, restoreSession, setAuthInitializing]);

  if (isAuthInitializing) {
    return <div className="min-h-screen bg-[#F8FAFC]" />;
  }

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
        {/* <ReactQueryDevtools initialIsOpen={false} /> */}
      </QueryClientProvider>
    </StrictMode>
  );
}
