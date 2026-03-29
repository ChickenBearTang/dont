import { Outlet } from 'react-router-dom';
import Header from '@/shared/components/Header';

import type { UserProfile } from '@/features/auth/types';

interface AppLayoutProps {
  user: UserProfile | null;
  onLogout: () => void;
  isAuthenticated: boolean;
}


const AppLayout = ({ user, onLogout, isAuthenticated }: AppLayoutProps) => {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col relative w-full pt-[64px]">
      <Header user={user} onLogout={onLogout} isAuthenticated={isAuthenticated} />
      <main className="flex-1 w-full max-w-7xl mx-auto px-6 lg:px-10 py-8 animate-[fadeInEffect_0.5s_ease-out_forwards] flex flex-col">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
