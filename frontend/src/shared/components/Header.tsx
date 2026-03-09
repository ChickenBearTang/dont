import React from 'react';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  userData: any; // TODO: Replace 'any' with the specific UserData type when extracted
  onLogout: () => void;
  isAuthenticated: boolean;
}

/**
 * 전역 상단 네비게이션바 컴포넌트
 */
const Header = ({ userData, onLogout, isAuthenticated }: HeaderProps) => {
  const navigate = useNavigate();

  return (
    <header className="fixed top-0 left-0 right-0 h-[60px] bg-background border-b border-[#F0F4F8] z-50 flex justify-center w-full">
      <div className="w-full max-w-[480px] h-full flex items-center justify-between px-5">
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        >
          <div className="text-[24px] font-black text-primary-blue">
            DON'T
          </div>
        </div>

        {isAuthenticated && (
          <div className="flex ml-10 flex-1 h-full font-bold">
            {['홈', '세이브박스', '소비리포트', '랭킹', '커뮤니티'].map((tab) => (
              <div
                key={tab}
                className={`flex items-center justify-center px-4 cursor-pointer text-[15px] border-b-[3px] transition-colors ${
                  tab === '홈'
                    ? 'border-eel text-eel'
                    : 'border-transparent text-gray hover:text-eel'
                }`}
              >
                {tab}
              </div>
            ))}
          </div>
        )}

        {isAuthenticated ? (
          <div className="flex gap-5 items-center">
            <div className="relative cursor-pointer text-[20px] text-eel">
              🔔
              <span className="absolute top-[2px] right-[2px] w-[6px] h-[6px] bg-error-red rounded-full"></span>
            </div>
            <div
              className="cursor-pointer text-[20px] text-eel hover:text-primary-blue transition-colors"
              title="마이페이지"
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
