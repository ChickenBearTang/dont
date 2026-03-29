import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { AccountDetail } from '../types';

const BANK_ICONS: Record<string, string> = {
  신한은행: new URL('../../../../assets/banks/shinhan.png', import.meta.url).href,
  KB국민은행: new URL('../../../../assets/banks/kb.png', import.meta.url).href,
  국민은행: new URL('../../../../assets/banks/kb.png', import.meta.url).href,
  우리은행: new URL('../../../../assets/banks/uri.png', import.meta.url).href,
  하나은행: new URL('../../../../assets/banks/hana.png', import.meta.url).href,
  KEB하나은행: new URL('../../../../assets/banks/hana.png', import.meta.url).href,
  NH농협은행: new URL('../../../../assets/banks/noghyub.png', import.meta.url).href,
  농협은행: new URL('../../../../assets/banks/noghyub.png', import.meta.url).href,
  싸피은행: new URL('../../../../assets/banks/ssafy.png', import.meta.url).href,
  SSAFY은행: new URL('../../../../assets/banks/ssafy.png', import.meta.url).href,
  default: new URL('../../../../assets/banks/shinhan.png', import.meta.url).href,
};

const getBankIcon = (bankName: string) => {
  return BANK_ICONS[bankName] || BANK_ICONS['default'];
};

interface AccountCardProps {
  account: AccountDetail;
}


export const AccountCard: React.FC<AccountCardProps> = ({ account }) => {
  const navigate = useNavigate();
  const { bankName, accountName, accountNo, accountBalance, currencyCode } = account;


  const formattedBalance = Number(accountBalance).toLocaleString();


  const handleCardClick = () => {
    navigate(`/account/${account.id}`);
  };

  return (
    <div
      onClick={handleCardClick}
      className="w-full p-5 lg:p-6 transition-all bg-white border border-light-gray rounded-2xl hover:shadow-md hover:border-primary-blue/30 cursor-pointer group flex flex-col md:flex-row md:items-center justify-between gap-4"
    >
      <div className="flex items-center gap-5">
        <div className="w-16 h-16 shrink-0 shadow-sm border border-gray-100 rounded-full bg-white flex items-center justify-center overflow-hidden group-hover:scale-105 transition-transform">
          <img
            src={getBankIcon(bankName)}
            alt={bankName}
            className="w-full h-full object-cover scale-[1.2]"
            onError={(e) => {
              const target = e.currentTarget as HTMLImageElement;
              if (target.src !== BANK_ICONS['default']) {
                target.src = BANK_ICONS['default'];
              }
            }}
          />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[12px] font-black tracking-tight text-gray-500 bg-gray-100 px-2 py-0.5 rounded-md">
              {bankName}
            </span>
          </div>
          <h3 className="text-[17px] font-extrabold text-eel group-hover:text-primary-blue transition-colors tracking-tight">
            {accountName}
          </h3>
          <p className="text-[13px] text-gray-400 font-mono mt-0.5">{accountNo}</p>
        </div>
      </div>

      <div className="flex flex-col items-end pl-[76px] md:pl-0">
        <div className="flex items-baseline justify-end gap-1">
          <span className="text-[24px] font-black tracking-tighter text-eel group-hover:text-primary-blue transition-colors">
            {formattedBalance}
          </span>
          <span className="text-[14px] font-bold text-gray-500">{currencyCode || '원'}</span>
        </div>
      </div>
    </div>
  );
};
