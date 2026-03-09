import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';

/**
 * 앱 내부 페이지 레이아웃 (헤더 포함)
 * 대시보드 및 이후 기능 서비스 전용
 */
const AppLayout = ({ userData, onLogout, isAuthenticated }) => {
  return (
    <div className="app">
      <Header userData={userData} onLogout={onLogout} isAuthenticated={isAuthenticated} />
      <main className="fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
