import { Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { logout as logoutApi } from '@/features/auth/api/authApi';


const PublicLayout = () => {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = async () => {
    try {
      await logoutApi();
    } catch (error) {
      void error;
    } finally {
      logout();
      navigate('/login', { replace: true });
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col relative w-full">
      {}
      <header className="h-[64px] flex items-center justify-between px-6 lg:px-10 max-w-7xl w-full mx-auto">
        <h1
          className="text-[28px] font-black text-primary-blue tracking-tighter cursor-pointer"
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        >
          DON'T
        </h1>
        {isAuthenticated && (
          <button
            className="px-4 py-2 text-[13px] font-bold text-eel border-b-2 border-eel hover:text-primary-blue hover:border-primary-blue transition-colors"
            onClick={() => void handleLogout()}
          >
            로그아웃
          </button>
        )}
      </header>
      <main className="flex-1 flex flex-col w-full animate-[fadeInEffect_0.5s_ease-out_forwards]">
        <div className="w-full h-full flex flex-col flex-1 justify-center">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default PublicLayout;
