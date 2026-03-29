import { useState } from 'react';
import type { ReportReasonCode, ReportTargetType } from '../types';
import { createReport } from '../api/communityApi';
import { useUIStore } from '@/shared/store/useUIStore';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetType: ReportTargetType;
  targetId: number;
}

const REASONS: { code: ReportReasonCode; label: string }[] = [
  { code: 'SPAM', label: '스팸/홍보' },
  { code: 'ABUSE', label: '욕설/비하' },
  { code: 'INAPPROPRIATE', label: '부적절한 콘텐츠' },
  { code: 'SCAM', label: '사기/거짓 정보' },
  { code: 'PRIVACY', label: '개인정보 노출' },
  { code: 'OTHER', label: '기타' },
];

export const ReportModal = ({ isOpen, onClose, targetType, targetId }: ReportModalProps) => {
  const [reasonCode, setReasonCode] = useState<ReportReasonCode | ''>('');
  const [detailText, setDetailText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { addToast } = useUIStore();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reasonCode) return;

    if (reasonCode === 'OTHER' && !detailText.trim()) {
      addToast('기타 사유 선택 시 상세 내용을 입력해 주세요.', 'info');
      return;
    }

    setSubmitting(true);
    try {
      await createReport({
        targetType,
        targetId,
        reasonCode: reasonCode as ReportReasonCode,
        detailText: detailText.trim() || undefined,
      });
      addToast('신고가 접수되었습니다. 검토 후 조치하겠습니다.', 'success');
      onClose();

      setReasonCode('');
      setDetailText('');
    } catch {
      addToast('신고 제출에 실패했습니다. 다시 시도해 주세요.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {}
      <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
          <h2 className="text-[18px] font-bold text-gray-900 tracking-tight">
            {targetType === 'POST' ? '게시글 신고' : '댓글 신고'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 -mr-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-5">
            <div>
              <label className="block text-[14px] font-bold text-gray-700 mb-3">
                신고 사유를 선택해 주세요
              </label>
              <div className="grid grid-cols-2 gap-2.5">
                {REASONS.map((reason) => (
                  <button
                    key={reason.code}
                    type="button"
                    onClick={() => setReasonCode(reason.code)}
                    className={`px-4 py-3 rounded-2xl text-[13.5px] font-semibold text-left transition-all border ${
                      reasonCode === reason.code
                        ? 'bg-rose-50 border-rose-200 text-rose-600 shadow-sm'
                        : 'bg-gray-50 border-transparent text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {reason.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-[14px] font-bold text-gray-700 mb-2.5">
                상세 내용 <span className="text-gray-400 font-medium">(선택)</span>
              </label>
              <textarea
                value={detailText}
                onChange={(e) => setDetailText(e.target.value)}
                placeholder="상세 내용을 입력해 주세요..."
                className="w-full h-32 p-4 text-[14px] bg-gray-50 border border-transparent rounded-2xl focus:bg-white focus:border-blue-500 outline-none resize-none transition-all placeholder:text-gray-400"
              />
            </div>
          </div>

          <div className="mt-8 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-4 bg-gray-100 hover:bg-gray-200 text-gray-600 font-bold rounded-2xl transition-colors text-[15px]"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={!reasonCode || submitting}
              className="flex-1 px-6 py-4 bg-rose-500 hover:bg-rose-600 disabled:bg-gray-200 text-white font-bold rounded-2xl transition-all shadow-lg shadow-rose-200 disabled:shadow-none text-[15px]"
            >
              {submitting ? '제출 중...' : '신고하기'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
