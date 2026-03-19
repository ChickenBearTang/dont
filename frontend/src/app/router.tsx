import { Navigate, createBrowserRouter } from 'react-router-dom';
import PublicLayout from '@/shared/components/PublicLayout';
import { SignUpPage, LoginPage } from '@/features/auth';
import { OnboardingPage } from '@/features/user';
import {
  AuthenticatedLayoutRoute,
  DashboardRoute,
  HomeRoute,
  PrCreateRoute,
  PrDetailRoute,
} from '@/app/routeComponents';

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
      {
        path: '/community/pr/new',
        element: <PrCreateRoute />,
      },
      {
        path: '/community/pr/:postId',
        element: <PrDetailRoute />,
      },
      {
        path: '/community',
        async lazy() {
          const { CommunityLayout } =
            await import('@/features/community/components/CommunityLayout');
          return { Component: CommunityLayout };
        },
        children: [
          {
            index: true,
            async lazy() {
              const { CommunityPage } = await import('@/features/community/pages/CommunityPage');
              return { Component: CommunityPage };
            },
          },
          {
            path: 'write',
            async lazy() {
              const { CreatePostPage } = await import('@/features/community/pages/CreatePostPage');
              return { Component: CreatePostPage };
            },
          },
          {
            path: 'poll',
            element: <Navigate to="/community?category=POLL" replace />,
          },
          {
            path: ':postId',
            async lazy() {
              const { PostDetailPage } = await import('@/features/community/pages/PostDetailPage');
              return { Component: PostDetailPage };
            },
          },
          {
            path: ':postId/edit',
            async lazy() {
              const { EditPostPage } = await import('@/features/community/pages/EditPostPage');
              return { Component: EditPostPage };
            },
          },
        ],
      },
    ],
  },
]);
