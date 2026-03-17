import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card } from '@/shared/components';
import { closePr, getPrDetail, submitPrVote } from '@/features/community/pr';
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

const getStatusBadgeClass = (status: string): string => {
  if (status === 'OPEN') return 'bg-blue-50 text-blue-700 border-blue-200';
  if (status === 'MERGED') return 'bg-green-50 text-green-700 border-green-200';
  return 'bg-gray-100 text-gray-700 border-gray-200';
};

export const PrDetailPage = () => {
  const navigate = useNavigate();
  const { postId } = useParams<{ postId: string }>();
  const { addToast } = useUIStore();

  const parsedPostId = useMemo(() => Number(postId), [postId]);

  const [detail, setDetail] = useState<PrDetailResponseData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [voteOpinion, setVoteOpinion] = useState('');
  const [isSubmittingVote, setIsSubmittingVote] = useState(false);
  const [isClosingPr, setIsClosingPr] = useState(false);

  const loadDetail = useCallback(async () => {
    if (!parsedPostId || Number.isNaN(parsedPostId)) {
      setErrorMessage('Invalid PR id.');
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
      setErrorMessage('Failed to load PR detail.');
    } finally {
      setIsLoading(false);
    }
  }, [parsedPostId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const handleVote = async (voteValue: 'AGREE' | 'DISAGREE') => {
    if (!detail || detail.status !== 'OPEN' || isSubmittingVote) return;

    setIsSubmittingVote(true);
    try {
      await submitPrVote(detail.postId, {
        voteValue,
        opinionText: voteOpinion.trim() || undefined,
      });
      addToast('Vote submitted.', 'success');
      setVoteOpinion('');
      await loadDetail();
    } catch {
      addToast('Failed to submit vote.', 'error');
    } finally {
      setIsSubmittingVote(false);
    }
  };

  const handleClosePr = async (resultStatus: 'MERGED' | 'CLOSED') => {
    if (!detail || detail.status !== 'OPEN' || isClosingPr) return;

    setIsClosingPr(true);
    try {
      await closePr(detail.postId, { resultStatus });
      addToast(`PR closed as ${resultStatus}.`, 'success');
      await loadDetail();
    } catch {
      addToast('Failed to close PR. Only author can close it.', 'error');
    } finally {
      setIsClosingPr(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-56 bg-gray-100 rounded-xl animate-pulse" />
        <Card className="h-64 animate-pulse bg-gray-50 border-gray-100">
          <div className="h-full" />
        </Card>
      </div>
    );
  }

  if (errorMessage || !detail) {
    return (
      <Card className="flex flex-col items-center gap-4 text-center py-12">
        <h2 className="text-xl font-black text-gray-800">PR detail error</h2>
        <p className="text-gray-500 font-medium">{errorMessage ?? 'Unexpected error.'}</p>
        <Button
          type="button"
          className="!w-auto px-6 py-2.5 text-sm"
          onClick={() => void loadDetail()}
        >
          Retry
        </Button>
      </Card>
    );
  }

  const isOpen = detail.status === 'OPEN';

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
      <section className="xl:col-span-8 space-y-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-gray-900">Purchase Request #{detail.postId}</h1>
            <span
              className={`px-3 py-1 rounded-full border text-xs font-bold ${getStatusBadgeClass(detail.status)}`}
            >
              {detail.status}
            </span>
          </div>
          <button
            type="button"
            className="px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-bold text-gray-700 hover:bg-gray-50 transition-colors"
            onClick={() => navigate('/community/pr/new')}
          >
            New PR
          </button>
        </div>

        <div className="relative pl-8">
          <div className="absolute left-3 top-0 bottom-0 w-px bg-gray-200" />

          <div className="relative mb-5">
            <span className="absolute -left-[25px] top-3 w-5 h-5 rounded-full bg-primary-blue border-4 border-white shadow" />
            <Card className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-xl font-black text-gray-900">{detail.itemName}</h2>
                <p className="text-sm font-bold text-gray-700">
                  {formatCurrency(detail.priceAmount)}
                </p>
              </div>
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{detail.content}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
                <p>
                  <span className="font-bold text-gray-900">Category:</span>{' '}
                  {detail.category ?? '-'}
                </p>
                <p>
                  <span className="font-bold text-gray-900">Result:</span>{' '}
                  {detail.resultStatus ?? '-'}
                </p>
              </div>
            </Card>
          </div>

          <div className="relative">
            <span className="absolute -left-[25px] top-3 w-5 h-5 rounded-full bg-gray-300 border-4 border-white shadow" />
            <Card className="space-y-3">
              <h3 className="text-lg font-black text-gray-900">Status Event</h3>
              <p className="text-sm text-gray-600">
                This PR is currently{' '}
                <span className="font-bold text-gray-900">{detail.status}</span>.
              </p>
              <p className="text-sm text-gray-600">
                Closed at:{' '}
                <span className="font-bold text-gray-900">{formatDateTime(detail.closedAt)}</span>
              </p>
            </Card>
          </div>
        </div>
      </section>

      <aside className="xl:col-span-4 space-y-4 xl:sticky xl:top-24">
        <Card className="space-y-3">
          <h3 className="text-lg font-black text-gray-900">Target Item</h3>
          {detail.imageUrl ? (
            <img
              src={detail.imageUrl}
              alt={detail.itemName}
              className="w-full h-44 object-cover rounded-xl border border-gray-100"
            />
          ) : (
            <div className="w-full h-44 rounded-xl border border-dashed border-gray-300 bg-gray-50 flex items-center justify-center text-sm font-bold text-gray-400">
              No image
            </div>
          )}
          <p className="font-bold text-gray-900 text-sm">{detail.itemName}</p>
          <p className="text-2xl font-black text-gray-900">{formatCurrency(detail.priceAmount)}</p>
          {detail.purchaseUrl ? (
            <a
              href={detail.purchaseUrl}
              target="_blank"
              rel="noreferrer"
              className="block text-center rounded-lg bg-[#0f172a] text-white text-sm font-bold py-3 hover:bg-[#1e293b] transition-colors"
            >
              Open purchase link
            </a>
          ) : (
            <p className="text-sm text-gray-500">No purchase link</p>
          )}
        </Card>

        <Card className="space-y-3">
          <h3 className="text-lg font-black text-gray-900">Review Votes</h3>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500"
              style={{
                width:
                  detail.totalVoteCount > 0
                    ? `${(detail.agreeCount / detail.totalVoteCount) * 100}%`
                    : '0%',
              }}
            />
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <p className="font-bold text-green-700">Approve {detail.agreeCount}</p>
            <p className="font-bold text-red-700">Reject {detail.disagreeCount}</p>
            <p className="font-bold text-gray-900">Total {detail.totalVoteCount}</p>
          </div>
          <textarea
            className="w-full min-h-[88px] rounded-xl border border-gray-200 px-3 py-2 text-sm outline-none focus:border-primary-blue"
            placeholder="Leave your opinion (optional)"
            value={voteOpinion}
            onChange={(event) => setVoteOpinion(event.target.value)}
            disabled={!isOpen || isSubmittingVote}
            maxLength={1000}
          />
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              className="!py-2.5 text-sm !bg-green-600 hover:!bg-green-700 disabled:!bg-gray-300"
              onClick={() => void handleVote('AGREE')}
              disabled={!isOpen || isSubmittingVote}
            >
              Approve
            </Button>
            <Button
              type="button"
              className="!py-2.5 text-sm !bg-red-600 hover:!bg-red-700 disabled:!bg-gray-300"
              onClick={() => void handleVote('DISAGREE')}
              disabled={!isOpen || isSubmittingVote}
            >
              Reject
            </Button>
          </div>
          {!isOpen && (
            <p className="text-xs text-gray-500 font-medium">Closed PR cannot receive votes.</p>
          )}
        </Card>

        <Card className="space-y-2">
          <h3 className="text-lg font-black text-gray-900">Close PR</h3>
          <p className="text-xs text-gray-500 font-medium">
            Only the author can close this PR. Backend will validate permission.
          </p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              className="!py-2.5 text-sm !bg-emerald-600 hover:!bg-emerald-700 disabled:!bg-gray-300"
              onClick={() => void handleClosePr('MERGED')}
              disabled={!isOpen || isClosingPr}
            >
              MERGED
            </Button>
            <Button
              type="button"
              className="!py-2.5 text-sm !bg-slate-600 hover:!bg-slate-700 disabled:!bg-gray-300"
              onClick={() => void handleClosePr('CLOSED')}
              disabled={!isOpen || isClosingPr}
            >
              CLOSED
            </Button>
          </div>
        </Card>
      </aside>
    </div>
  );
};
