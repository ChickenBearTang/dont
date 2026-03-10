import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppLayout from '@/shared/components/AppLayout';
import PublicLayout from '@/shared/components/PublicLayout';
import { SignUpPage, LoginPage } from '@/features/auth';
import { OnboardingPage } from '@/features/user';
import { DashboardPage } from '@/pages/DashboardPage';

import type { UserProfile } from '@/features/auth/types';

export const createRouter = (isAuthenticated: boolean, user: UserProfile | null, handleLogout: () => void) => {
  return createBrowserRouter([
    {
      element: <PublicLayout />,
      children: [
        {
          path: '/',
          element: isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />
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
      element: <AppLayout user={user} onLogout={handleLogout} isAuthenticated={isAuthenticated} />,
      children: [
        {
          path: '/dashboard',
          element: isAuthenticated ? <DashboardPage /> : <Navigate to="/" />
        }
      ]
    }
  ]);
};
