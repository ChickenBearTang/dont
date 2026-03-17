import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Button } from '@/shared/components';
import { getPrDetail, submitPrVote } from '@/features/community/pr';
import type { PrDetailResponseData } from '@/features/community/pr';
import { useUIStore } from '@/shared/store/useUIStore';

const formatCurrency = (value: number): string =>
  new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);

const formatDateTime = (value: string | null): string => {
  if (!value) return '-';
  return new Date(value).toLocaleString('ko-KR');
};

const statusStyleMap: Record<string, string> = {
  OPEN: 'bg-blue-50 text-blue-700',
  MERGED: 'bg-green-50 text-green-700',
  CLOSED: 'bg-gray-100 text-gray-700',
};

export const PrDetailPage = () => {
  const { postId } = useParams<{ postId: string }>();
  const { addToast } = useUIStore();

  const parsedPostId = useMemo(() => Number(postId), [postId]);

  const [detail, setDetail] = useState<PrDetailResponseData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [voteOpinion, setVoteOpinion] = useState('');
  const [isSubmittingVote, setIsSubmittingVote] = useState(false);

  const loadDetail = useCallback(async () => {
    if (!parsedPostId || Number.isNaN(parsedPostId)) {
      setErrorMessage('유효하지 않은 PR ID입니다.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await getPrDetail(parsedPostId);
      setDetail(response.data);
    } catch {
      setDetail(null);
      setErrorMessage('PR 상세 정보를 불러오지 못했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [parsedPostId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const handleVote = async (voteValue: 'AGREE' | 'DISAGREE') => {
    if (!detail || detail.status !== 'OPEN' || isSubmittingVote) {
      return;
    }

    setIsSubmittingVote(true);
    try {
      await submitPrVote(detail.postId, {
        voteValue,
        opinionText: voteOpinion.trim() || undefined,
      });
      addToast('투표가 반영되었습니다.', 'success');
      setVoteOpinion('');
      await loadDetail();
    } catch {
      addToast('투표 처리에 실패했습니다. 잠시 후 다시 시도해주세요.', 'error');
    } finally {
      setIsSubmittingVote(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-48 bg-gray-100 rounded-xl animate-pulse" />
        <Card className="h-48 animate-pulse bg-gray-50 border-gray-100">
          <div className="h-full" />
        </Card>
      </div>
    );
  }

  if (errorMessage || !detail) {
    return (
      <Card className="flex flex-col items-center gap-4 text-center py-12">
        <h2 className="text-xl font-black text-gray-800">PR 상세 조회 실패</h2>
        <p className="text-gray-500 font-medium">
          {errorMessage ?? '알 수 없는 오류가 발생했습니다.'}
        </p>
        <Button
          type="button"
          className="!w-auto px-6 py-2.5 text-sm"
          onClick={() => addToast(errorMessage ?? '잠시 후 다시 시도해주세요.', 'error')}
        >
          확인
        </Button>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <Card className="space-y-4">
          <div className="flex items-center justify-between gap-3">
            <h1 className="text-2xl font-black text-gray-900">{detail.itemName}</h1>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold ${statusStyleMap[detail.status] ?? statusStyleMap.CLOSED}`}
            >
              {detail.status}
            </span>
          </div>
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{detail.content}</p>
        </Card>
      </div>

      <div className="space-y-6">
        <Card className="space-y-3">
          <h2 className="text-lg font-black text-gray-900">요청 정보</h2>
          <div className="space-y-2 text-sm text-gray-700">
            <p>
              <span className="font-bold text-gray-900">가격</span>{' '}
              {formatCurrency(detail.priceAmount)}
            </p>
            <p>
              <span className="font-bold text-gray-900">카테고리</span> {detail.category ?? '-'}
            </p>
            <p>
              <span className="font-bold text-gray-900">구매 링크</span>{' '}
              {detail.purchaseUrl ? (
                <a
                  href={detail.purchaseUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary-blue underline underline-offset-2 break-all"
                >
                  {detail.purchaseUrl}
                </a>
              ) : (
                '-'
              )}
            </p>
            <p>
              <span className="font-bold text-gray-900">결과 상태</span>{' '}
              {detail.resultStatus ?? '-'}
            </p>
            <p>
              <span className="font-bold text-gray-900">종료 시각</span>{' '}
              {formatDateTime(detail.closedAt)}
            </p>
          </div>
        </Card>

        <Card className="space-y-3">
          <h2 className="text-lg font-black text-gray-900">투표 현황</h2>
          <div className="space-y-2 text-sm text-gray-700">
            <p>
              <span className="font-bold text-green-700">찬성</span> {detail.agreeCount}표
            </p>
            <p>
              <span className="font-bold text-red-700">반대</span> {detail.disagreeCount}표
            </p>
            <p>
              <span className="font-bold text-gray-900">총 참여</span> {detail.totalVoteCount}표
            </p>
          </div>

          <div className="pt-2 space-y-3">
            <textarea
              className="w-full min-h-[88px] rounded-xl border border-gray-200 px-3 py-2 text-sm outline-none focus:border-primary-blue"
              placeholder="의견을 남기면 함께 저장됩니다. (선택)"
              value={voteOpinion}
              onChange={(event) => setVoteOpinion(event.target.value)}
              disabled={detail.status !== 'OPEN' || isSubmittingVote}
              maxLength={1000}
            />
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                className="!py-2.5 text-sm !bg-green-600 hover:!bg-green-700 disabled:!bg-gray-300"
                onClick={() => void handleVote('AGREE')}
                disabled={detail.status !== 'OPEN' || isSubmittingVote}
              >
                찬성
              </Button>
              <Button
                type="button"
                className="!py-2.5 text-sm !bg-red-600 hover:!bg-red-700 disabled:!bg-gray-300"
                onClick={() => void handleVote('DISAGREE')}
                disabled={detail.status !== 'OPEN' || isSubmittingVote}
              >
                반대
              </Button>
            </div>
            {detail.status !== 'OPEN' && (
              <p className="text-xs text-gray-500 font-medium">종료된 PR은 투표할 수 없습니다.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
