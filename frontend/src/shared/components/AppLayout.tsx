import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '@/shared/components/Header';

interface AppLayoutProps {
  userData: any; // TODO: Replace 'any' with the specific UserData type when extracted
  onLogout: () => void;
  isAuthenticated: boolean;
}

/**
 * 앱 내부 페이지 레이아웃 (헤더 포함)
 * 대시보드 및 이후 기능 서비스 전용
 */
const AppLayout = ({ userData, onLogout, isAuthenticated }: AppLayoutProps) => {
  return (
    <div className="max-w-[480px] mx-auto min-h-screen bg-background shadow-[0_0_20px_rgba(0,0,0,0.05)] flex flex-col relative w-full">
      <Header userData={userData} onLogout={onLogout} isAuthenticated={isAuthenticated} />
      <main className="flex-1 flex flex-col animate-[fadeInEffect_0.5s_ease-out_forwards]">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
