import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Input, Button } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
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
  const addToast = useUIStore((state) => state.addToast);

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
      // eslint-disable-next-line react-hooks/set-state-in-effect
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
      setError(
        '주계좌 또는 세이브박스를 찾을 수 없습니다. 세이브박스가 개설되어 있는지 확인해 주세요.'
      );
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
          addToast('저축 설정이 성공적으로 저장되었습니다! 🎉', 'success');
          navigate('/finance/savebox');
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
        <p className="text-text-muted font-bold">기존 설정을 불러오고 있습니다...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12 relative">
      <button
        onClick={() => navigate('/finance/savebox')}
        className="flex items-center gap-2 text-gray-400 hover:text-eel font-bold mb-8 transition-colors relative z-10"
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
        세이브박스로 돌아가기
      </button>

      <div className="absolute inset-0 bg-pattern-dots opacity-30 z-0 pointer-events-none" />
      <div className="mb-10 text-center relative z-10">
        <div className="inline-block px-4 py-1.5 bg-accent-soft text-primary-blue rounded-full text-[13px] font-black mb-4 uppercase tracking-[0.05em] shadow-sm">
          Auto Savings
        </div>
        <h1 className="text-3xl lg:text-[2.5rem] font-black text-eel mb-4 tracking-tight leading-tight">
          어떤 결제를 할 때마다
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-blue to-accent drop-shadow-sm">
            자동으로 저축
          </span>
          할까요?
        </h1>
        <p className="text-text-muted font-bold">
          자주 이용하는 결제 키워드를 등록하면,
          <br />
          해당 결제가 발생할 때마다 정해진 금액을 세이브박스에 모아드려요.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
        {/* Keyword Card */}
        <Card className="!p-8 !rounded-[32px]">
          <Input
            label="결제처 키워드"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="예: 커피, 택시, 배달의민족"
            inputClassName="pl-12 font-black"
          />
          <p className="mt-3 ml-2 text-xs text-text-subtle font-bold">
            * 입력하신 단어가 포함된 결제 내역이 생기면 저축이 실행됩니다.
          </p>
        </Card>

        {/* Amount Card */}
        <Card className="!p-8 !rounded-[32px]">
          <Input
            label="1회 저축 금액"
            type="number"
            step="10000"
            min="0"
            value={amount || ''}
            onChange={(e) => {
              const val = e.target.value;
              if (Number(val) < 0) return;
              setAmount(Number(val));
            }}
            placeholder="0"
            inputClassName="text-right pr-9 font-black text-2xl text-primary-blue leading-none"
            unit="원"
          />
        </Card>

        {/* Toggle Card */}
        <Card className="!p-8 !rounded-[32px] flex items-center justify-between">
          <div>
            <label className="block text-[14px] font-black text-eel tracking-tight ml-1">
              저축 상태 설정
            </label>
            <p className="text-[13px] text-text-subtle font-bold ml-1 mt-1">
              지금 바로 자동 저축을 시작할까요?
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsActive(!isActive)}
            className={`w-[60px] h-[32px] rounded-full transition-all duration-300 relative shadow-inner ${
              isActive
                ? 'bg-gradient-to-r from-primary-blue to-accent shadow-blue-200/50'
                : 'bg-surface-soft border border-line-soft'
            }`}
          >
            <div
              className={`absolute top-[3px] w-[24px] h-[24px] bg-white rounded-full transition-all duration-300 shadow-sm ${
                isActive ? 'left-[33px]' : 'left-[3px]'
              }`}
            />
          </button>
        </Card>

        {error && (
          <div className="p-4 bg-error-red/5 text-error-red border border-error-red/20 rounded-[20px] text-center text-[14px] font-bold animate-shake backdrop-blur-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Submit Button */}
        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full !py-[18px] !text-[17px] !rounded-[24px] shadow-[0_12px_30px_rgba(10,101,255,0.2)] mt-8"
        >
          {isSubmitting ? '설정 저장 중...' : '저축 설정 완료하기'}
        </Button>
      </form>
    </div>
  );
};
