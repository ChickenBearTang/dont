import React from 'react';
import { Modal } from '@/shared/components/Modal';
import { motion } from 'framer-motion';

interface RankingSyncModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isSyncing: boolean;
}


export const RankingSyncModal: React.FC<RankingSyncModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isSyncing,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="🔄 랭킹 갱신">
      <div className="p-2">
        <div className="mb-6 text-center">
          <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-blue-100/50">
            <motion.svg
              animate={isSyncing ? { rotate: 360 } : {}}
              transition={isSyncing ? { repeat: Infinity, duration: 2, ease: "linear" } : {}}
              className="w-8 h-8 text-primary-blue"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </motion.svg>
          </div>
          <p className="text-eel font-bold text-lg mb-2">실시간 데이터 동기화</p>
          <p className="text-gray-500 text-sm leading-relaxed">
            현재 모든 유저의 실시간 잔액을 기반으로 랭킹을 다시 계산하시겠습니까?<br />
            <span className="text-xs font-semibold text-primary-blue/70">(동기화에 수 초가 소요될 수 있습니다)</span>
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-8">
          <button
            onClick={onClose}
            disabled={isSyncing}
            className="py-4 bg-gray-100 text-gray-500 rounded-2xl font-black hover:bg-gray-200 transition-all active:scale-95 disabled:opacity-50"
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            disabled={isSyncing}
            className={`py-4 rounded-2xl font-black transition-all active:scale-95 shadow-lg ${
              isSyncing
                ? 'bg-blue-200 text-white cursor-not-allowed'
                : 'bg-primary-blue text-white shadow-blue-100 hover:bg-blue-600'
            }`}
          >
            {isSyncing ? '동기화 중...' : '갱신하기'}
          </button>
        </div>
      </div>
    </Modal>
  );
};
