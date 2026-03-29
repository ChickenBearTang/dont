import { Navigate, Outlet } from 'react-router-dom';
import { useEffect, useState } from 'react';
import AppLayout from '@/shared/components/AppLayout';
import { LoginPage } from '@/features/auth';
import { DashboardPage } from '@/pages/DashboardPage';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { logout as logoutApi } from '@/features/auth/api/authApi';
import { PrDetailPage } from '@/features/community/pr';
import { fetchOnboardingStatus } from '@/features/user/api/userApi';

const AuthLoadingFallback = () => <div className="min-h-screen bg-surface-page" />;

export const HomeRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />;
};

export const RequireAuthRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

export const RequireAdminRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const role = useAuthStore((state) => state.user?.role);

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (role !== 'ADMIN') {
    return <Navigate to="/community" replace />;
  }

  return <Outlet />;
};

export const RequireCompletedOnboardingRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [status, setStatus] = useState<'loading' | 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED'>(
    'loading'
  );

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const load = async () => {
      try {
        const response = await fetchOnboardingStatus();
        const nextStatus = response.data.onboardingStatus;
        if (
          nextStatus === 'COMPLETED' ||
          nextStatus === 'IN_PROGRESS' ||
          nextStatus === 'NOT_STARTED'
        ) {
          setStatus(nextStatus);
          return;
        }
        setStatus('NOT_STARTED');
      } catch {
        setStatus('NOT_STARTED');
      }
    };

    void load();
  }, [isAuthenticated]);

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (status === 'loading') {
    return <div className="min-h-screen bg-surface-page" />;
  }

  if (status !== 'COMPLETED') {

    if (window.location.pathname === '/dashboard') {
      return <Outlet />;
    }
    return <Navigate to={status === 'NOT_STARTED' ? '/onboarding' : '/finance-connect'} replace />;
  }

  return <Outlet />;
};

export const AuthenticatedLayoutRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = async () => {
    try {
      await logoutApi();
    } catch (error) {
      void error;
    } finally {
      logout();
    }
  };

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <AppLayout user={user} onLogout={handleLogout} isAuthenticated={isAuthenticated} />;
};

export const DashboardRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  return isAuthenticated ? <DashboardPage /> : <Navigate to="/" replace />;
};

export const PrDetailRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  return isAuthenticated ? <PrDetailPage /> : <Navigate to="/" replace />;
};

export const PrCreateRoute = () => {
  const isAuthInitializing = useAuthStore((state) => state.isAuthInitializing);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthInitializing) {
    return <AuthLoadingFallback />;
  }

  return isAuthenticated ? (
    <Navigate to="/community/write?category=PR" replace />
  ) : (
    <Navigate to="/" replace />
  );
};
