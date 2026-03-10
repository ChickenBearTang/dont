import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppLayout from '@/shared/components/AppLayout';
import PublicLayout from '@/shared/components/PublicLayout';
import { SignUpPage, LoginPage } from '@/features/auth';
import { OnboardingPage } from '@/features/user';
import { DashboardPage } from '@/pages/DashboardPage';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

const HomeRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />;
};

const AuthenticatedLayoutRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return <AppLayout user={user} onLogout={logout} isAuthenticated={isAuthenticated} />;
};

const DashboardRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <DashboardPage /> : <Navigate to="/" replace />;
};

export const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      {
        path: '/',
        element: <HomeRoute />
      },
      {
        path: '/login',
        element: <LoginPage />
      },
      {
        path: '/onboarding',
        element: <OnboardingPage />
      },
      {
        path: '/signup',
        element: <SignUpPage />
      },
      {
        path: '/finance-connect',
        element: <div>FinanceConnect Placeholder</div>
      },
      {
        path: '/loading',
        element: <div>LoadingScreen Placeholder</div>
      },
      {
        path: '/savebox-setup',
        element: <div>SaveboxSetup Placeholder</div>
      },
      {
        path: '/success',
        element: <div>SuccessScreen Placeholder</div>
      }
    ]
  },
  {
    element: <AuthenticatedLayoutRoute />,
    children: [
      {
        path: '/dashboard',
        element: <DashboardRoute />
      }
    ]
  }
]);
