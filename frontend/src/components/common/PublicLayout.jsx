import React from 'react';
import { Outlet } from 'react-router-dom';

/**
 * 공개 페이지 레이아웃 (헤더 없음)
 * 랜딩, 로그인, 온보딩 등 전용
 */
const PublicLayout = () => {
  return (
    <div className="app">
      <main
        className="fade-in"
        style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh' }}
      >
        <Outlet />
      </main>
    </div>
  );
};

export default PublicLayout;
