import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { AccountDetail } from '../types';

interface AccountCardProps {
  account: AccountDetail;
}

/**
 * 개별 계좌 정보를 표시하는 카드 컴포넌트
 */
export const AccountCard: React.FC<AccountCardProps> = ({ account }) => {
  const navigate = useNavigate();
  const { bankName, accountName, accountNo, accountBalance, currencyCode } = account;

  // 잔액 포맷팅 (콤마 추가)
  const formattedBalance = Number(accountBalance).toLocaleString();

  // 계좌 클릭 시 상세 페이지로 이동
  const handleCardClick = () => {
    navigate(`/account/${account.id}`);
  };

  return (
    <div
      onClick={handleCardClick}
      className="w-full p-6 transition-all bg-white border border-light-gray rounded-2xl hover:shadow-lg hover:border-primary-blue/30 cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray mb-1">{bankName}</span>
          <h3 className="text-lg font-bold text-eel group-hover:text-primary-blue transition-colors">
            {accountName}
          </h3>
          <p className="text-sm text-gray font-mono">{accountNo}</p>
        </div>
        <div className="p-2 rounded-full bg-blue-bg">
          <div className="w-6 h-6 rounded-full bg-primary-blue/20 flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-primary-blue" />
          </div>
        </div>
      </div>

      <div className="flex items-baseline justify-end gap-1 mt-6">
        <span className="text-2xl font-black text-eel">{formattedBalance}</span>
        <span className="text-lg font-bold text-eel">{currencyCode || '원'}</span>
      </div>

      <div className="w-full h-1 mt-4 rounded-full bg-light-gray overflow-hidden">
        <div className="w-2/3 h-full bg-primary-blue/30" />
      </div>
    </div>
  );
};
