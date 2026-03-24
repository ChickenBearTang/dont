import { Navigate, Outlet } from 'react-router-dom';
import { useEffect, useState } from 'react';
import AppLayout from '@/shared/components/AppLayout';
import { LoginPage } from '@/features/auth';
import { DashboardPage } from '@/pages/DashboardPage';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { logout as logoutApi } from '@/features/auth/api/authApi';
import { PrDetailPage } from '@/features/community/pr';
import { fetchOnboardingStatus } from '@/features/user/api/userApi';

export const HomeRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />;
};

export const RequireAuthRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

export const RequireCompletedOnboardingRoute = () => {
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

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (status === 'loading') {
    return <div className="min-h-screen bg-surface-page" />;
  }

  if (status !== 'COMPLETED') {
    return <Navigate to={status === 'NOT_STARTED' ? '/onboarding' : '/finance-connect'} replace />;
  }

  return <Outlet />;
};

export const AuthenticatedLayoutRoute = () => {
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

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <AppLayout user={user} onLogout={handleLogout} isAuthenticated={isAuthenticated} />;
};

export const DashboardRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <DashboardPage /> : <Navigate to="/" replace />;
};

export const PrDetailRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <PrDetailPage /> : <Navigate to="/" replace />;
};

export const PrCreateRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Navigate to="/community/write?category=PR" replace /> : <Navigate to="/" replace />;
};
