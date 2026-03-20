import React, { useState } from 'react';
import { Modal } from '@/shared/components/Modal';
import { useExecuteManualSavings } from '../hooks/useAccountMutations';

interface ManualSavingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  primaryAccountName?: string;
  saveboxAccountName?: string;
}

/**
 * 수동 저축(지금 채우기) 금액 입력 모달
 */
export const ManualSavingsModal: React.FC<ManualSavingsModalProps> = ({
  isOpen,
  onClose,
  primaryAccountName = '주계좌',
  saveboxAccountName = '세이브박스',
}) => {
  const [amount, setAmount] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const { mutate: executeSavings, isPending } = useExecuteManualSavings();

  const handleSavings = () => {
    const numericAmount = Number(amount);
    setError(null);

    // 시니어 디테일: 유효성 검사 (0원 이하 방지)
    if (!amount || numericAmount <= 0) {
      setError('저축할 금액을 0원보다 크게 입력해 주세요.');
      return;
    }

    // 시니어 디테일: 따닥 방지(isPending)은 버튼에서 처리
    executeSavings(numericAmount, {
      onSuccess: () => {
        alert(`${numericAmount.toLocaleString()}원이 성공적으로 저축되었습니다! ✨`);
        setAmount('');
        onClose();
      },
      onError: () => {
        setError('저축 처리 중 오류가 발생했습니다. 다시 시도해 주세요.');
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

        <div className="mb-6">
          <label className="block text-sm font-black text-eel mb-3">저축할 금액</label>
          <div className="relative">
            <input
              type="number"
              value={amount}
              onChange={(e) => {
                setAmount(e.target.value);
                setError(null);
              }}
              placeholder="0"
              className="w-full px-5 py-4 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-primary-blue/30 transition-all font-black text-2xl text-primary-blue text-right pr-12"
              autoFocus
            />
            <span className="absolute right-5 top-1/2 -translate-y-1/2 font-bold text-eel text-lg">
              원
            </span>
          </div>
          {error && (
            <p className="mt-2 text-xs text-error-red font-bold animate-shake">⚠️ {error}</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 mt-10">
          <button
            onClick={onClose}
            className="py-4 bg-gray-100 text-gray-500 rounded-2xl font-black hover:bg-gray-200 transition-all active:scale-95"
          >
            취소
          </button>
          <button
            onClick={handleSavings}
            disabled={isPending}
            className={`py-4 rounded-2xl font-black transition-all active:scale-95 shadow-lg ${
              isPending
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-primary-blue text-white shadow-blue-100 hover:bg-blue-600'
            }`}
          >
            {isPending ? '처리 중...' : '저축하기'}
          </button>
        </div>
      </div>
    </Modal>
  );
};
