import { createBrowserRouter } from 'react-router-dom';
import PublicLayout from '@/shared/components/PublicLayout';
import { ForgotPasswordPage, SignUpPage, LoginPage } from '@/features/auth';
import { FinanceConnectPage, MyPagePage, OnboardingPage } from '@/features/user';
import NotFoundPage from '@/shared/components/NotFoundPage';
import ServerErrorPage from '@/shared/components/ServerErrorPage';
import {
  AuthenticatedLayoutRoute,
  DashboardRoute,
  HomeRoute,
  PrCreateRoute,
  PrDetailRoute,
  RequireAdminRoute,
  RequireAuthRoute,
  RequireCompletedOnboardingRoute,
} from '@/app/routeComponents';

export const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    errorElement: <ServerErrorPage />,
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
        path: '/signup',
        element: <SignUpPage />,
      },
      {
        path: '/forgot-password',
        element: <ForgotPasswordPage />,
      },
      {
        element: <RequireAuthRoute />,
        children: [
          {
            path: '/onboarding',
            element: <OnboardingPage />,
          },
          {
            path: '/finance-connect',
            element: <FinanceConnectPage />,
          },
          {
            path: '/finance/savebox-setup',
            async lazy() {
              const { SaveboxSetupPage } =
                await import('@/features/finance/account/pages/SaveboxSetupPage');
              return { Component: SaveboxSetupPage };
            },
          },
          {
            path: '/finance/savings-rule-setup',
            async lazy() {
              const { SavingsRuleSetupPage } =
                await import('@/features/finance/account/pages/SavingsRuleSetupPage');
              return { Component: SavingsRuleSetupPage };
            },
          },
          {
            path: '/loading',
            element: <div>LoadingScreen Placeholder</div>,
          },
          {
            path: '/success',
            element: <div>SuccessScreen Placeholder</div>,
          },
        ],
      },
    ],
  },
  {
    element: <RequireCompletedOnboardingRoute />,
    children: [
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
                  const { CommunityPage } =
                    await import('@/features/community/pages/CommunityPage');
                  return { Component: CommunityPage };
                },
              },
              {
                path: 'write',
                async lazy() {
                  const { CreatePostPage } =
                    await import('@/features/community/pages/CreatePostPage');
                  return { Component: CreatePostPage };
                },
              },
              {
                path: ':postId',
                async lazy() {
                  const { PostDetailPage } =
                    await import('@/features/community/pages/PostDetailPage');
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
          {
            path: '/finance/cards',
            async lazy() {
              const { CardListPage } = await import('@/features/finance/card');
              return { Component: CardListPage };
            },
          },
          {
            path: '/finance/cards/:cardId',
            async lazy() {
              const { CardDetailPage } = await import('@/features/finance/card');
              return { Component: CardDetailPage };
            },
          },
          {
            path: '/finance/cards/recommendation',
            async lazy() {
              const { CardRecommendationRankPage } = await import('@/features/finance/card/pages/CardRecommendationRankPage');
              return { Component: CardRecommendationRankPage };
            },
          },
          {
            path: '/finance/cards/recommendation/:recommendCardId',
            async lazy() {
              const { CardRecommendationDetailPage } = await import('@/features/finance/card/pages/CardRecommendationDetailPage');
              return { Component: CardRecommendationDetailPage };
            },
          },
          {
            path: '/account',
            async lazy() {
              const { AccountPage } = await import('@/features/finance/account/pages/AccountPage');
              return { Component: AccountPage };
            },
          },
          {
            path: '/account/:accountId',
            async lazy() {
              const { AccountDetailPage } =
                await import('@/features/finance/account/pages/AccountDetailPage');
              return { Component: AccountDetailPage };
            },
          },
          {
            path: '/finance/report',
            async lazy() {
              const { MonthlyReportPage } = await import('@/features/finance/report');
              return { Component: MonthlyReportPage };
            },
          },
          {
            path: '/finance',
            async lazy() {
              const { FinanceHomePage } = await import('@/features/finance/pages/FinanceHomePage');
              return { Component: FinanceHomePage };
            },
          },
          {
            path: '/mypage',
            element: <MyPagePage />,
          },
          {
            path: '/finance/savebox',
            async lazy() {
              const { SaveboxDetailPage } =
                await import('@/features/finance/account/pages/SaveboxDetailPage');
              return { Component: SaveboxDetailPage };
            },
          },
          {
            path: '/savings-rule-setup',
            async lazy() {
              const { SavingsRuleSetupPage } =
                await import('@/features/finance/account/pages/SavingsRuleSetupPage');
              return { Component: SavingsRuleSetupPage };
            },
          },
          {
            element: <RequireAdminRoute />,
            children: [
              {
                path: '/admin/reports',
                async lazy() {
                  const { default: AdminReportPage } =
                    await import('@/features/community/pages/AdminReportPage');
                  return { Component: AdminReportPage };
                },
              },
            ],
          },
          {
            path: '/ranking',
            async lazy() {
              const { RankingPage } = await import('@/features/ranking/pages/RankingPage');
              return { Component: RankingPage };
            },
          },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
  {
    path: '/500',
    element: <ServerErrorPage />,
  },
]);
