import React from 'react';
import { AccountList } from '../components/AccountList';

export const AccountPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <div className="max-w-3xl px-4 py-12 mx-auto">
        <header className="mb-10 text-center md:text-left">
          <h1 className="text-3xl font-black text-eel mb-2">내 계좌</h1>
          <p className="text-lg text-gray">연결된 모든 계좌 정보를 한눈에 확인하고 관리하세요.</p>
        </header>

        <main>
          <AccountList />
        </main>

        <footer className="mt-16 text-center text-sm text-gray/50 pb-8">
          © 2026 Awesome Project Finance Inc.
        </footer>
      </div>
    </div>
  );
};
