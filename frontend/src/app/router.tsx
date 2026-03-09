import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppLayout from '@/shared/components/AppLayout';
import PublicLayout from '@/shared/components/PublicLayout';

// TODO: 아래 주석 처리된 도메인 컴포넌트들은 아직 파일이 흩어져있거나 생성되지 않았습니다.
// features/ 하위로 파일 이동 및 TS 변환이 끝나면 이 주석을 풀고 연결합니다!
// import { Landing, Login, Signup } from '@/features/auth';
// import { Onboarding, FinanceConnect, LoadingScreen, SaveboxSetup, SuccessScreen } from '@/features/user';
// import { Dashboard } from '@/features/analytics';

export const createRouter = (isAuthenticated: boolean, userData: any, handleLogout: () => void) => {
  return createBrowserRouter([
    {
      element: <PublicLayout />,
      children: [
        {
          path: '/',
          element: isAuthenticated ? <Navigate to="/dashboard" /> : <div>Landing Placeholder</div>
        },
        {
          path: '/login',
          element: <div>Login Placeholder</div>
        },
        {
          path: '/onboarding',
          element: <div>Onboarding Placeholder</div>
        },
        {
          path: '/signup',
          element: <div>Signup Placeholder</div>
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
      element: <AppLayout userData={userData} onLogout={handleLogout} isAuthenticated={isAuthenticated} />,
      children: [
        {
          path: '/dashboard',
          // element: isAuthenticated ? <Dashboard userData={userData} onLogout={handleLogout} /> : <Navigate to="/" />
          element: isAuthenticated ? <div>대시보드 임시 화면 (연결 필요)</div> : <Navigate to="/" />
        }
      ]
    }
  ]);
};
