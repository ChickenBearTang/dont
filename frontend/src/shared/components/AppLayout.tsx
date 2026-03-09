import { Outlet } from 'react-router-dom';
import Header from '@/shared/components/Header';

import type { UserProfile } from '@/features/auth/types';

interface AppLayoutProps {
  user: UserProfile | null;
  onLogout: () => void;
  isAuthenticated: boolean;
}

/**
 * 앱 내부 페이지 레이아웃 (헤더 포함)
 * 대시보드 및 이후 기능 서비스 전용
 */
const AppLayout = ({ user, onLogout, isAuthenticated }: AppLayoutProps) => {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col relative w-full pt-[64px]">
      <Header user={user} onLogout={onLogout} isAuthenticated={isAuthenticated} />
      <main className="flex-1 w-full max-w-7xl mx-auto px-6 lg:px-10 py-8 animate-[fadeInEffect_0.5s_ease-out_forwards]">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
