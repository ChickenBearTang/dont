import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetSavingsSetting, useGetMyAccounts } from '../hooks/useAccountQueries';
import { useSaveSavingsSetting } from '../hooks/useAccountMutations';

/**
 * 자동 저축 규칙 설정 페이지
 */
export const SavingsRuleSetupPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: initialSetting, isLoading: isFetchingSetting } = useGetSavingsSetting();
  const { data: accounts, isLoading: isFetchingAccounts } = useGetMyAccounts();
  const { mutate: saveSetting, isPending: isSubmitting } = useSaveSavingsSetting();

  // Identification Logic: Find real accounts
  // Primary: First non-savebox account
  // Savebox: First account with '세이브박스' in name or type
  const primaryAccount = accounts?.find(
    (a) => !a.accountName.includes('세이브박스') && !a.accountTypeName.includes('세이브박스')
  );
  const saveboxAccount = accounts?.find(
    (a) => a.accountName.includes('세이브박스') || a.accountTypeName.includes('세이브박스')
  );

  const isFetching = isFetchingSetting || isFetchingAccounts;

  // Form states
  const [keyword, setKeyword] = useState('');
  const [amount, setAmount] = useState<number>(0);
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load existing settings into form
  useEffect(() => {
    if (initialSetting) {
      setKeyword(initialSetting.keyword || '');
      setAmount(initialSetting.savingsAmount || 0);
      setIsActive(initialSetting.isActive ?? true);
    }
  }, [initialSetting]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!keyword.trim()) {
      setError('저축할 결제 키워드를 입력해 주세요.');
      return;
    }
    if (amount <= 0) {
      setError('저축 금액은 0원보다 커야 합니다.');
      return;
    }

    if (!primaryAccount || !saveboxAccount) {
      setError('주계좌 또는 세이브박스를 찾을 수 없습니다. 세이브박스가 개설되어 있는지 확인해 주세요.');
      return;
    }

    // Submit with real IDs
    saveSetting(
      {
        primaryAccountId: primaryAccount.id,
        saveboxAccountId: saveboxAccount.id,
        keyword: keyword.trim(),
        savingsAmount: amount,
        isActive,
      },
      {
        onSuccess: () => {
          alert('저축 설정이 성공적으로 저장되었습니다! 🎉');
          navigate('/finance'); // 금융 홈으로 이동
        },
        onError: () => {
          setError('설정 저장 중 오류가 발생했습니다. 다시 시도해 주세요.');
        },
      }
    );
  };

  if (isFetching) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-blue-100 border-t-primary-blue rounded-full animate-spin mb-4" />
        <p className="text-gray-500 font-medium">기존 설정을 불러오고 있습니다...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <div className="mb-10 text-center">
        <div className="inline-block px-4 py-1.5 bg-blue-50 text-primary-blue rounded-full text-xs font-black mb-4 uppercase tracking-wider">
          Auto Savings
        </div>
        <h1 className="text-3xl lg:text-4xl font-black text-eel mb-4 tracking-tight">
          어떤 결제를 할 때마다<br />
          <span className="text-primary-blue">자동으로 저축</span>할까요?
        </h1>
        <p className="text-gray font-medium">
          자주 이용하는 결제 키워드를 등록하면,<br />
          해당 결제가 발생할 때마다 정해진 금액을 세이브박스에 모아드려요.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Keyword Card */}
        <div className="bg-white p-8 rounded-[32px] border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300">
          <label className="block text-sm font-black text-eel mb-4">결제처 키워드</label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-xl">🔍</span>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="예: 커피, 택시, 배달의민족"
              className="w-full pl-12 pr-4 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-primary-blue/30 transition-all font-bold text-eel placeholder:text-gray-300"
            />
          </div>
          <p className="mt-3 text-xs text-gray-400 font-medium">
            * 입력하신 단어가 포함된 결제 내역이 생기면 저축이 실행됩니다.
          </p>
        </div>

        {/* Amount Card */}
        <div className="bg-white p-8 rounded-[32px] border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300">
          <label className="block text-sm font-black text-eel mb-4">1회 저축 금액</label>
          <div className="relative">
            <input
              type="number"
              value={amount || ''}
              onChange={(e) => setAmount(Number(e.target.value))}
              placeholder="0"
              className="w-full px-5 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-primary-blue/30 transition-all font-black text-2xl text-primary-blue text-right pr-12"
            />
            <span className="absolute right-5 top-1/2 -translate-y-1/2 font-bold text-eel text-lg">원</span>
          </div>
        </div>

        {/* Toggle Card */}
        <div className="bg-white p-8 rounded-[32px] border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300 flex items-center justify-between">
          <div>
            <label className="block text-sm font-black text-eel mb-1">저축 상태 설정</label>
            <p className="text-xs text-gray-400 font-medium">지금 바로 자동 저축을 시작할까요?</p>
          </div>
          <button
            type="button"
            onClick={() => setIsActive(!isActive)}
            className={`w-14 h-8 rounded-full transition-all duration-500 relative ${
              isActive ? 'bg-primary-blue shadow-lg shadow-blue-200' : 'bg-gray-200'
            }`}
          >
            <div
              className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-all duration-500 shadow-sm ${
                isActive ? 'left-7' : 'left-1'
              }`}
            />
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-error-red rounded-2xl text-center text-sm font-bold animate-shake">
            ⚠️ {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-5 rounded-[24px] font-black text-lg transition-all transform active:scale-95 shadow-xl ${
            isSubmitting
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-primary-blue text-white hover:bg-blue-600 shadow-blue-200 hover:shadow-blue-300'
          }`}
        >
          {isSubmitting ? '설정 저장 중...' : '저축 설정 완료하기'}
        </button>
      </form>
    </div>
  );
};
