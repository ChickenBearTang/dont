import type { UserProfile } from '@/features/auth/types';
import { useNavigate, useLocation } from 'react-router-dom';

interface HeaderProps {
  user: UserProfile | null;
  onLogout: () => void;
  isAuthenticated: boolean;
}

/**
 * 전역 상단 네비게이션바 컴포넌트
 */
const Header = ({ user, onLogout, isAuthenticated }: HeaderProps) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <header className="fixed top-0 left-0 right-0 h-[64px] bg-white/80 backdrop-blur-md border-b border-gray-100 z-50 flex justify-center w-full transition-all">
      <div className="w-full max-w-7xl h-full flex items-center justify-between px-6 lg:px-10">
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        >
          <div className="text-[24px] font-black text-primary-blue">DON'T</div>
        </div>

        {isAuthenticated && (
          <nav className="hidden md:flex ml-12 flex-1 h-full font-bold gap-1">
            {[
              { label: '홈', path: '/dashboard' },
              { label: '세이브박스', path: '/savebox-setup' },
              { label: '소비리포트', path: '/finance-connect' },
              { label: '랭킹', path: '/ranking' },
              { label: '커뮤니티', path: '/community' },
            ].map((tab) => {
              const isActive = location.pathname.startsWith(tab.path);
              return (
                <div
                  key={tab.label}
                  onClick={() => navigate(tab.path)}
                  className={`flex items-center justify-center px-5 cursor-pointer text-[15px] border-b-[3px] transition-all duration-300 hover:text-primary-blue ${
                    isActive
                      ? 'border-primary-blue text-primary-blue'
                      : 'border-transparent text-gray-500 hover:border-gray-200'
                  }`}
                >
                  {tab.label}
                </div>
              );
            })}
          </nav>
        )}

        {isAuthenticated ? (
          <div className="flex gap-5 items-center">
            <div className="relative cursor-pointer text-[20px] text-eel">
              🔔
              <span className="absolute top-[2px] right-[2px] w-[6px] h-[6px] bg-error-red rounded-full"></span>
            </div>
            <div
              className="cursor-pointer text-[20px] text-eel hover:text-primary-blue transition-colors"
              title={user?.nickname ? `${user.nickname}님의 마이페이지` : '마이페이지'}
            >
              👤
            </div>
            <button
              className="px-3 py-1.5 text-[13px] font-bold text-eel border-b-2 border-eel hover:text-primary-blue hover:border-primary-blue transition-colors ml-2.5"
              onClick={onLogout}
            >
              로그아웃
            </button>
          </div>
        ) : (
          <div className="flex gap-2.5">
            <button
              className="px-4 py-2 text-[13px] font-bold text-eel border-b-2 border-eel hover:text-primary-blue hover:border-primary-blue transition-colors"
              onClick={() => navigate('/login')}
            >
              로그인
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
