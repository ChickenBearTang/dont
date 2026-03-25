import { Outlet } from 'react-router-dom';
import { CommunitySidebar } from './CommunitySidebar';
import StrictSecretaryModal from '@/components/StrictSecretaryModal';

export const CommunityLayout = () => {
  return (
    <div className="flex gap-6 lg:gap-8 w-full mx-auto items-start max-w-7xl">
      <aside className="w-[200px] lg:w-[240px] flex-shrink-0 sticky top-[88px]">
        <CommunitySidebar />
      </aside>
      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
      <StrictSecretaryModal />
    </div>
  );
};
