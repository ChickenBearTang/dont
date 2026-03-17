import { createBrowserRouter } from 'react-router-dom';
import PublicLayout from '@/shared/components/PublicLayout';
import { SignUpPage, LoginPage } from '@/features/auth';
import { OnboardingPage } from '@/features/user';
import { AuthenticatedLayoutRoute, DashboardRoute, HomeRoute } from '@/app/routeComponents';

export const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      {
        path: '/',
        element: <HomeRoute />,
      },
      {
        path: '/login',
        element: <LoginPage />,
      },
      {
        path: '/onboarding',
        element: <OnboardingPage />,
      },
      {
        path: '/signup',
        element: <SignUpPage />,
      },
      {
        path: '/finance-connect',
        element: <div>FinanceConnect Placeholder</div>,
      },
      {
        path: '/loading',
        element: <div>LoadingScreen Placeholder</div>,
      },
      {
        path: '/savebox-setup',
        element: <div>SaveboxSetup Placeholder</div>,
      },
      {
        path: '/success',
        element: <div>SuccessScreen Placeholder</div>,
      },
    ],
  },
  {
    element: <AuthenticatedLayoutRoute />,
    children: [
      {
        path: '/dashboard',
        element: <DashboardRoute />,
      },
    ],
  },
]);

