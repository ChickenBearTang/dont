import React, { useState } from 'react';
import { Modal } from '@/shared/components/Modal';
import { useUIStore } from '@/shared/store/useUIStore';
import { useExecuteManualSavings } from '../hooks/useAccountMutations';

interface ManualSavingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  primaryAccountName?: string;
  saveboxAccountName?: string;
}


export const ManualSavingsModal: React.FC<ManualSavingsModalProps> = ({
  isOpen,
  onClose,
  primaryAccountName = '주계좌',
  saveboxAccountName = '세이브박스',
}) => {
  const [amount, setAmount] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [step, setStep] = useState<'amount' | 'password'>('amount');
  const [error, setError] = useState<string | null>(null);
  const { mutate: executeSavings, isPending } = useExecuteManualSavings();
  const addToast = useUIStore((state) => state.addToast);

  const handleNextStep = () => {
    const numericAmount = Number(amount);
    if (!amount || numericAmount <= 0) {
      setError('저축할 금액을 0원보다 크게 입력해 주세요.');
      return;
    }
    setError(null);
    setStep('password');
  };

  const handleSavings = () => {
    if (!password) {
      setError('비밀번호를 입력해 주세요.');
      return;
    }

    const numericAmount = Number(amount);
    executeSavings({ amount: numericAmount, password }, {
      onSuccess: () => {
        addToast(`${numericAmount.toLocaleString()}원이 성공적으로 저축되었습니다! ✨`, 'success');
        setAmount('');
        setPassword('');
        setStep('amount');
        onClose();
      },
      onError: (err: any) => {

        const errorMsg = err?.response?.data?.message || '저축 처리 중 오류가 발생했습니다.';
        setError(errorMsg);
      },
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="💰 지금 바로 저축하기">
      <div className="p-2">
        <div className="mb-8 text-center bg-blue-50/50 py-4 rounded-2xl border border-blue-100/50">
          <div className="flex items-center justify-center gap-4">
            <span className="font-bold text-eel text-sm">{primaryAccountName}</span>
            <span className="text-primary-blue animate-pulse">➔</span>
            <span className="font-bold text-primary-blue text-sm">{saveboxAccountName}</span>
          </div>
        </div>

        {step === 'amount' ? (
          <div className="mb-6 animate-fade-in">
            <label className="block text-sm font-black text-eel mb-3">저축할 금액</label>
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
                className="w-full px-5 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-primary-blue/30 transition-all font-black text-2xl text-primary-blue text-right pr-12"
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
              className="w-full px-5 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-primary-blue/30 transition-all font-black text-2xl text-center tracking-widest text-primary-blue"
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
            onClick={step === 'amount' ? handleNextStep : handleSavings}
            disabled={isPending}
            className={`py-4 rounded-2xl font-black transition-all active:scale-95 shadow-lg ${isPending
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-primary-blue text-white shadow-blue-100 hover:bg-blue-600'
              }`}
          >
            {isPending ? '처리 중...' : step === 'amount' ? '다음' : '저축하기'}
          </button>
        </div>
      </div>
    </Modal>
  );
};
