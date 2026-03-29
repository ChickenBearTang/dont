import { AccountList } from '../components/AccountList';
import { useRefreshAccounts } from '../hooks/useAccountMutations';
import { useGetMyAccounts, useGetSavingsSetting } from '../hooks/useAccountQueries';
import { AccountCard } from '../components/AccountCard';
import { useNavigate } from 'react-router-dom';


export const AccountPage: React.FC = () => {
  const navigate = useNavigate();
  const { mutate: refreshAccounts, isPending } = useRefreshAccounts();
  const { data: accounts, isLoading: isLoadingAccounts } = useGetMyAccounts();
  const { data: setting, isLoading: isLoadingSetting } = useGetSavingsSetting();

  const handleRefresh = () => {
    refreshAccounts();
  };


  const primaryAccount = accounts?.find((a) => a.id === setting?.primaryAccountId);

  if (isLoadingAccounts || isLoadingSetting) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-blue-100 border-t-primary-blue rounded-full animate-spin mb-4" />
        <p className="text-gray-500 font-medium">계좌 정보를 불러오고 있습니다...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <div className="max-w-3xl px-4 py-12 mx-auto">
        <button
          onClick={() => navigate('/finance')}
          className="flex items-center gap-2 text-gray-400 hover:text-eel font-bold mb-8 transition-colors"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          금융 홈으로
        </button>

        {}
        <header className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="text-center md:text-left">
            <h1 className="text-3xl font-black text-eel mb-2">내 계좌</h1>
            <p className="text-lg text-gray">연결된 모든 계좌 정보를 한눈에 확인하고 관리하세요.</p>
          </div>

          <button
            onClick={handleRefresh}
            disabled={isPending}
            className="group flex items-center justify-center gap-2 px-6 py-3 bg-white border border-gray-100 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-100 transition-all active:scale-95 disabled:opacity-70 disabled:pointer-events-none"
          >
            <span
              className={`text-xl transition-transform duration-700 ${isPending ? 'animate-spin' : 'group-hover:rotate-180'}`}
            >
              🔄
            </span>
            <span className="text-sm font-black text-eel">
              {isPending ? '최신화 중...' : '최신 내역 불러오기'}
            </span>
          </button>
        </header>

        {}
        {primaryAccount && (
          <section className="mb-12">
            <div className="flex items-center gap-2 mb-4 px-2">
              <span className="text-xs font-black text-primary-blue bg-blue-50 px-2 py-0.5 rounded-md uppercase">
                주계좌
              </span>
              <h2 className="text-xl font-black text-eel">나의 주계좌</h2>
            </div>
            <div className="scale-100 ring-4 ring-primary-blue/5 rounded-3xl overflow-hidden shadow-xl shadow-blue-100/20">
              <AccountCard account={primaryAccount} />
            </div>
          </section>
        )}

        {}
        <main>
          <AccountList />
        </main>

        {}
        <footer className="mt-16 text-center text-sm text-gray/50 pb-8">
          © 2026 Awesome Project Finance Inc.
        </footer>
      </div>
    </div>
  );
};
