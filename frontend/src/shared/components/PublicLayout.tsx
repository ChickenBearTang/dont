import React from 'react';
import { Outlet } from 'react-router-dom';

/**
 * 공개 페이지 레이아웃 (헤더 없음)
 * 랜딩, 로그인, 온보딩 등 전용
 */
const PublicLayout = () => {
  return (
    <div className="max-w-[480px] mx-auto min-h-screen bg-background shadow-[0_0_20px_rgba(0,0,0,0.05)] flex flex-col relative w-full">
      <main className="flex-1 flex flex-col min-h-screen animate-[fadeInEffect_0.5s_ease-out_forwards]">
        <Outlet />
      </main>
    </div>
  );
};

export default PublicLayout;
