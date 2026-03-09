import { Outlet } from 'react-router-dom';

/**
 * 공개 페이지 레이아웃 (헤더 없음)
 * 랜딩, 로그인, 온보딩 등 전용
 */
const PublicLayout = () => {
  return (
    <div className="min-h-screen bg-white flex flex-col relative w-full">
      {/* 글로벌 네비게이션 느낌의 심플 헤더 */}
      <header className="h-[64px] flex items-center px-6 lg:px-10 max-w-7xl w-full mx-auto">
        <h1 className="text-[28px] font-black text-primary-blue tracking-tighter cursor-pointer">DON'T</h1>
      </header>
      <main className="flex-1 flex flex-col items-center justify-center animate-[fadeInEffect_0.5s_ease-out_forwards] py-10">
        <div className="w-full max-w-[1200px] px-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default PublicLayout;
