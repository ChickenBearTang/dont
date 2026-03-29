import React, { useState, useEffect } from 'react';

interface ReportProcessModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (note: string) => Promise<void>;
  type: 'blind' | 'reject';
  reasonLabel?: string;
  detailText?: string;
}

export const ReportProcessModal: React.FC<ReportProcessModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  type,
  reasonLabel,
  detailText,
}) => {
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setNote('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(note);
      onClose();
    } catch (error) {
      console.error('Failed to process report:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const isBlind = type === 'blind';
  const actionName = isBlind ? '블라인드' : '기각';

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
            신고 처리: {actionName}
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
            {}
            {(reasonLabel || detailText) && (
              <div className="p-4 bg-orange-50 border border-orange-100 rounded-2xl">
                <label className="block text-[12px] font-bold text-orange-800 mb-1 uppercase tracking-wider">
                  접수된 신고 사유
                </label>
                <div className="text-[14px] font-bold text-orange-950">
                  {reasonLabel || '사유 없음'}
                </div>
                {detailText && (
                  <div className="mt-2 text-[13px] text-orange-800/80 leading-relaxed bg-white/50 p-2.5 rounded-xl border border-orange-200/50">
                    {detailText}
                  </div>
                )}
              </div>
            )}

            <div
              className={`p-4 rounded-2xl ${isBlind ? 'bg-blue-bg text-secondary-blue' : 'bg-blue-bg text-secondary-blue'} text-sm leading-relaxed border border-blue-100/50`}
            >
              {isBlind ? (
                <p>
                  <strong>블라인드 처리 시</strong> 해당 콘텐츠가 즉시 숨김 처리되며, 사용자들에게
                  노출되지 않습니다.
                </p>
              ) : (
                <p>
                  <strong>기각 처리 시</strong> 접수된 신고가 타당하지 않다고 판단하여 무시하며,
                  해당 콘텐츠는 그대로 유지됩니다.
                </p>
              )}
            </div>

            <div>
              <label className="block text-[14px] font-bold text-gray-700 mb-2.5">
                처리 사유 <span className="text-gray-400 font-medium">(선택 사항)</span>
              </label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder={`${actionName} 처리 사유를 입력해 주세요...`}
                className="w-full h-32 p-4 text-[14px] bg-light-gray border border-transparent rounded-2xl focus:bg-white focus:border-primary-blue outline-none resize-none transition-all placeholder:text-gray-400"
              />
            </div>
          </div>

          <div className="mt-8 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-4 bg-light-gray hover:bg-gray text-eel font-bold rounded-2xl transition-colors text-[15px]"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={`flex-1 px-6 py-4 ${
                isBlind
                  ? 'bg-error-red hover:opacity-90 shadow-red-100'
                  : 'bg-eel hover:opacity-90 shadow-gray-200'
              } text-white font-bold rounded-2xl transition-all shadow-lg text-[15px] disabled:opacity-50`}
            >
              {submitting ? '처리 중...' : `${actionName} 확정`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
