import { Navigate } from 'react-router-dom';
import AppLayout from '@/shared/components/AppLayout';
import { LoginPage } from '@/features/auth';
import { DashboardPage } from '@/pages/DashboardPage';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { logout as logoutApi } from '@/features/auth/api/authApi';
import { PrCreatePage, PrDetailPage } from '@/features/community/pr';

export const HomeRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />;
};

export const AuthenticatedLayoutRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = async () => {
    try {
      await logoutApi();
    } catch {
      // Keep local logout even if the server logout call fails.
    } finally {
      logout();
    }
  };

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
  return isAuthenticated ? <PrCreatePage /> : <Navigate to="/" replace />;
};
