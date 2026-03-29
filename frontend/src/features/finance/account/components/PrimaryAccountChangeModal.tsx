import React from 'react';
import { Modal } from '@/shared/components/Modal';
import { useUIStore } from '@/shared/store/useUIStore';
import { useGetMyAccounts } from '../hooks/useAccountQueries';
import { useSetPrimaryAccount } from '../hooks/useAccountMutations';

interface PrimaryAccountChangeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPrimaryAccountId?: number;
}


export const PrimaryAccountChangeModal: React.FC<PrimaryAccountChangeModalProps> = ({
  isOpen,
  onClose,
  currentPrimaryAccountId,
}) => {
  const { data: accounts, isLoading } = useGetMyAccounts();
  const { mutate: setPrimary, isPending } = useSetPrimaryAccount();
  const addToast = useUIStore((state) => state.addToast);


  const eligibleAccounts = accounts?.filter(
    (a) => !a.accountName.includes('세이브박스') && !a.accountTypeName.includes('세이브박스')
  );

  const handleSelect = (accountId: number) => {
    if (accountId === currentPrimaryAccountId) {
      onClose();
      return;
    }

    setPrimary(accountId, {
      onSuccess: () => {
        addToast('주계좌가 성공적으로 변경되었습니다. ✨', 'success');
        onClose();
      },
      onError: () => {
        addToast('주계좌 변경 중 오류가 발생했습니다.', 'error');
      },
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="🏦 주계좌 변경하기">
      <div className="py-2">
        <p className="text-sm text-gray mb-6 leading-relaxed">
          저축 규칙이 실행될 때 자금이 빠져나갈
          <br />
          새로운 주계좌를 선택해 주세요.
        </p>

        {isLoading ? (
          <div className="py-10 flex justify-center">
            <div className="w-8 h-8 border-4 border-blue-100 border-t-primary-blue rounded-full animate-spin" />
          </div>
        ) : (
          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
            {eligibleAccounts?.map((account) => (
              <button
                key={account.id}
                onClick={() => handleSelect(account.id)}
                disabled={isPending}
                className={`w-full p-5 rounded-2xl border-2 transition-all flex items-center justify-between group ${account.id === currentPrimaryAccountId
                  ? 'border-primary-blue bg-blue-50/30'
                  : 'border-gray-50 bg-white hover:border-primary-blue/30 hover:bg-gray-50/50'
                  }`}
              >
                <div className="text-left">
                  <span className="text-[10px] font-black text-gray-400 uppercase tracking-tighter block mb-1">
                    {account.bankName}
                  </span>
                  <h4 className="font-black text-eel group-hover:text-primary-blue transition-colors">
                    {account.accountName}
                  </h4>
                  <p className="text-xs text-gray-400 font-mono mt-0.5">{account.accountNo}</p>
                </div>

                <div className="text-right">
                  <div className="flex items-baseline gap-0.5">
                    <span className="font-black text-eel">
                      {Number(account.accountBalance).toLocaleString()}
                    </span>
                    <span className="text-[10px] font-bold text-gray-400">원</span>
                  </div>
                  {account.id === currentPrimaryAccountId && (
                    <span className="text-[10px] font-black text-primary-blue bg-blue-100 px-2 py-0.5 rounded-full mt-2 inline-block">
                      사용 중
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}

        <div className="mt-8">
          <button
            onClick={onClose}
            className="w-full py-4 bg-gray-100 text-gray-500 rounded-2xl font-black hover:bg-gray-200 transition-all"
          >
            취소
          </button>
        </div>
      </div>
    </Modal>
  );
};
