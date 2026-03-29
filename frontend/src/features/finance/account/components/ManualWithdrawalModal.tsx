import React, { useState } from 'react';
import { Modal } from '@/shared/components/Modal';
import { useUIStore } from '@/shared/store/useUIStore';
import { useExecuteManualWithdrawal } from '../hooks/useAccountMutations';

interface ManualWithdrawalModalProps {
  isOpen: boolean;
  onClose: () => void;
  primaryAccountName?: string;
  saveboxAccountName?: string;
  saveboxBalance?: number;
}


export const ManualWithdrawalModal: React.FC<ManualWithdrawalModalProps> = ({
  isOpen,
  onClose,
  primaryAccountName = '주계좌',
  saveboxAccountName = '세이브박스',
  saveboxBalance = 0,
}) => {
  const [amount, setAmount] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [step, setStep] = useState<'amount' | 'password'>('amount');
  const [error, setError] = useState<string | null>(null);
  const { mutate: executeWithdrawal, isPending } = useExecuteManualWithdrawal();
  const addToast = useUIStore((state) => state.addToast);

  const handleNextStep = () => {
    const numericAmount = Number(amount);
    if (!amount || numericAmount <= 0) {
      setError('출금할 금액을 0원보다 크게 입력해 주세요.');
      return;
    }
    if (numericAmount > saveboxBalance) {
      setError(`잔액이 부족합니다. (최대 ${saveboxBalance.toLocaleString()}원)`);
      return;
    }
    setError(null);
    setStep('password');
  };

  const handleWithdrawal = () => {
    if (!password) {
      setError('비밀번호를 입력해 주세요.');
      return;
    }

    const numericAmount = Number(amount);
    executeWithdrawal({ amount: numericAmount, password }, {
      onSuccess: () => {
        addToast(`${numericAmount.toLocaleString()}원을 성공적으로 꺼냈습니다. 💸`, 'success');
        setAmount('');
        setPassword('');
        setStep('amount');
        onClose();
      },
      onError: (err: any) => {

        const errorMsg = err?.response?.data?.message || '출금 처리 중 오류가 발생했습니다.';
        setError(errorMsg);
      },
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="💸 잔액 꺼내기">
      <div className="p-2">
        <div className="mb-8 text-center bg-amber-50/50 py-4 rounded-2xl border border-amber-100/50">
          <div className="flex items-center justify-center gap-4">
            <span className="font-bold text-amber-600 text-sm">{saveboxAccountName}</span>
            <span className="text-amber-500 animate-pulse">➔</span>
            <span className="font-bold text-eel text-sm">{primaryAccountName}</span>
          </div>
        </div>

        {step === 'amount' ? (
          <div className="mb-6 animate-fade-in">
            <div className="flex justify-between items-end mb-3">
              <label className="block text-sm font-black text-eel">출금할 금액</label>
              <span className="text-[11px] font-bold text-gray-400">
                꺼낼 수 있는 돈: {saveboxBalance.toLocaleString()}원
              </span>
            </div>
            <div className="relative">
              <input
                type="number"
                step="10000"
                min="0"
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value);
                  setError(null);
                }}
                placeholder="0"
                className="w-full px-5 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-amber-500/30 transition-all font-black text-2xl text-amber-600 text-right pr-12"
                autoFocus
              />
              <span className="absolute right-5 top-1/2 -translate-y-1/2 font-bold text-eel text-lg">원</span>
            </div>
          </div>
        ) : (
          <div className="mb-6 animate-slide-up">
            <label className="block text-sm font-black text-eel mb-3 text-center">🔐 보안을 위해 비밀번호를 입력해 주세요</label>
            <input
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError(null);
              }}
              placeholder="••••••••"
              className="w-full px-5 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-amber-500/30 transition-all font-black text-2xl text-center tracking-widest text-amber-600"
              autoFocus
            />
          </div>
        )}

        {error && (
          <p className="mt-2 text-xs text-error-red font-bold animate-shake text-center">⚠️ {error}</p>
        )}

        <div className="grid grid-cols-2 gap-3 mt-10">
          <button
            onClick={() => {
              if (step === 'password') {
                setStep('amount');
                setError(null);
              } else {
                onClose();
              }
            }}
            className="py-4 bg-gray-100 text-gray-500 rounded-2xl font-black hover:bg-gray-200 transition-all active:scale-95"
          >
            {step === 'password' ? '이전으로' : '취소'}
          </button>
          <button
            onClick={step === 'amount' ? handleNextStep : handleWithdrawal}
            disabled={isPending}
            className={`py-4 rounded-2xl font-black transition-all active:scale-95 shadow-lg ${isPending
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-amber-500 text-white shadow-amber-100 hover:bg-amber-600'
              }`}
          >
            {isPending ? '처리 중...' : step === 'amount' ? '다음' : '꺼내기'}
          </button>
        </div>
      </div>
    </Modal>
  );
};
