import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppLayout from '@/shared/components/AppLayout';
import PublicLayout from '@/shared/components/PublicLayout';

// TODO: 아래 주석 처리된 도메인 컴포넌트들은 아직 파일이 흩어져있거나 생성되지 않았습니다.
// features/ 하위로 파일 이동 및 TS 변환이 끝나면 이 주석을 풀고 연결합니다!
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
