import { StrictMode, useEffect, useRef } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import { refreshAccessToken } from '@/features/auth/api/authApi';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import '@/styles/index.css';

const AppBootstrap = () => {
  const hasBootstrappedRef = useRef(false);

  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const setAuthInitializing = useAuthStore((state) => state.setAuthInitializing);
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
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
        setAccessToken(nextToken);
      } catch {
        logout();
      } finally {
        setAuthInitializing(false);
      }
    };

    void bootstrapAuth();
  }, [logout, setAccessToken, setAuthInitializing]);

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
      <AppBootstrap />
    </StrictMode>
  );
}

