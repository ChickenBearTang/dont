import { StrictMode } from 'react';
import { RouterProvider } from 'react-router-dom';
import { createRouter } from '@/app/router';
import { ToastContainer } from '@/shared/components/ToastContainer';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import '@/styles/index.css';

export function App() {
  const { isAuthenticated, user, logout } = useAuthStore();
  
  const handleLogout = () => {
    logout();
  };

  // 현재 상태를 주입하여 라우터 인스턴스 생성
  const router = createRouter(isAuthenticated, user, handleLogout);

  return (
    <StrictMode>
      <ToastContainer />
      <RouterProvider router={router} />
    </StrictMode>
  );
}
