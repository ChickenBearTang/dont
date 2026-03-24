import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card } from '@/shared/components';
import { closePr, getPrDetail, submitPrVote } from '@/features/community/pr';
import type { PrDetailResponseData } from '@/features/community/pr';
import { useUIStore } from '@/shared/store/useUIStore';
import { formatRelativeTime } from '@/shared/utils/date';
import { UserAvatar } from '@/features/community/components/UserAvatar';

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

const formatAbsoluteDate = (value: string): string =>
  new Date(value).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

const normalizePrStatus = (status: string): string => status.trim().toUpperCase();

const getStatusBadgeClass = (status: string): string => {
  const normalizedStatus = normalizePrStatus(status);

  if (normalizedStatus === 'OPEN') return 'bg-blue-50 text-blue-700 border-blue-200';
  if (normalizedStatus === 'MERGED') return 'bg-green-50 text-green-700 border-green-200';
  if (normalizedStatus === 'CLOSED') return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

const getTimelineDotClass = (type: 'base' | 'review' | 'status', decision?: string): string => {
  if (type === 'review') {
    return decision === 'APPROVE' ? 'bg-success' : 'bg-danger';
  }
  if (type === 'status') return 'bg-accent';
  return 'bg-primary-blue';
};

interface TimelineEvent {
  id: string;
  type: 'base' | 'review' | 'status';
  title: string;
  subTitle: string;
  content: string;
  timeLabel: string;
  actorLabel?: string;
  decision?: string;
}

interface EventPayload {
  title?: string;
  itemName?: string;
  priceAmount?: number;
  decision?: string;
  voteValue?: string;
  opinionText?: string;
  before?: string;
  after?: string;
  closeReason?: string;
}

interface ContentSection {
  title: string;
  body: string;
}

const parseEventPayload = (payload: Record<string, unknown> | null): EventPayload => {
  if (!payload) return {};
  return payload as EventPayload;
};

const parseContentSections = (content: string): ContentSection[] => {
  const knownHeadings = ['왜 필요한가?', '예산은 적절한가?', '대체재는 없는가?'];
  const lines = content.split('\n');
  const sections: ContentSection[] = [];
  let currentTitle: string | null = null;
  let buffer: string[] = [];

  const flush = () => {
    if (!currentTitle) {
      return;
    }

    sections.push({
      title: currentTitle,
      body: buffer.join('\n').trim(),
    });
    buffer = [];
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (knownHeadings.includes(trimmed)) {
      flush();
      currentTitle = trimmed;
      return;
    }
    buffer.push(line);
  });

  flush();

  if (sections.length > 0) {
    return sections;
  }

  return [
    {
      title: '구매 요청 내용',
      body: content.trim(),
    },
  ];
};

const buildTimelineEvents = (detail: PrDetailResponseData): TimelineEvent[] => {
  if (detail.events && detail.events.length > 0) {
    return detail.events.map((event) => {
      const payload = parseEventPayload(event.payload);

      if (event.eventType === 'REVIEW_SUBMITTED') {
        const isApprove = payload.decision === 'APPROVE';
        const actorName = event.actorNickname ?? `사용자 #${event.actorUserId ?? '-'}`;
        const reviewSummary = isApprove
          ? `${actorName}님이 승인 의견을 남겼습니다.`
          : `${actorName}님이 변경 요청 의견을 남겼습니다.`;
        return {
          id: `event-${event.eventId}`,
          type: 'review',
          title: isApprove ? 'Approve 리뷰 등록' : 'Reject 리뷰 등록',
          subTitle: payload.decision ? `결정: ${payload.decision}` : '리뷰가 등록되었습니다.',
          content:
            payload.opinionText && payload.opinionText.trim().length > 0
              ? payload.opinionText
              : reviewSummary,
          timeLabel: formatRelativeTime(event.createdAt),
          actorLabel: event.actorNickname ?? undefined,
          decision: payload.decision,
        };
      }

      if (event.eventType === 'STATUS_CHANGED') {
        return {
          id: `event-${event.eventId}`,
          type: 'status',
          title: '상태 변경',
          subTitle:
            payload.before && payload.after
              ? `${payload.before} -> ${payload.after}`
              : `현재 상태: ${detail.status}`,
          content: payload.closeReason
            ? `종료 사유: ${payload.closeReason}`
            : '요청 상태가 변경되었습니다.',
          timeLabel: formatRelativeTime(event.createdAt),
          actorLabel: event.actorNickname ?? undefined,
        };
      }

      return {
        id: `event-${event.eventId}`,
        type: 'base',
        title: '구매 요청 생성',
        subTitle: `카테고리: ${detail.category ?? '미지정'}`,
        content:
          payload.title && payload.itemName ? `${payload.title} / ${payload.itemName}` : detail.title,
        timeLabel: formatRelativeTime(event.createdAt),
        actorLabel: event.actorNickname ?? undefined,
      };
    });
  }

  return [
    {
      id: 'base-fallback',
      type: 'base',
      title: '구매 요청 생성',
      subTitle: `카테고리: ${detail.category ?? '미지정'}`,
      content: detail.title,
      timeLabel: '요청 등록',
    },
    ...(detail.totalVoteCount > 0
      ? [
          {
            id: 'review-fallback',
            type: 'review' as const,
            title: '리뷰 투표 집계',
            subTitle: `Approve ${detail.agreeCount} / Reject ${detail.disagreeCount}`,
            content: '리뷰어 투표가 반영되었습니다.',
            timeLabel: `총 ${detail.totalVoteCount}명 참여`,
          },
        ]
      : []),
    ...(detail.status !== 'OPEN'
      ? [
          {
            id: 'status-fallback',
            type: 'status' as const,
            title: `요청 상태 변경 (${detail.status})`,
            subTitle: `현재 상태: ${detail.status}`,
            content: '해당 구매 요청은 종료되어 더 이상 리뷰를 받을 수 없습니다.',
            timeLabel: `종료 시각: ${formatDateTime(detail.closedAt)}`,
          },
        ]
      : []),
  ];
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
      setErrorMessage('유효하지 않은 PR 번호입니다.');
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
    if (!detail || detail.status !== 'OPEN' || isSubmittingVote) return;

    setIsSubmittingVote(true);
    try {
      await submitPrVote(detail.postId, {
        voteValue,
        opinionText: voteOpinion.trim() || undefined,
      });
      addToast('투표가 등록되었습니다.', 'success');
      setVoteOpinion('');
      await loadDetail();
    } catch {
      addToast('투표 등록에 실패했습니다.', 'error');
    } finally {
      setIsSubmittingVote(false);
    }
  };

  const handleClosePr = async (resultStatus: 'MERGED' | 'CLOSED') => {
    if (!detail || detail.status !== 'OPEN' || isClosingPr) return;

    setIsClosingPr(true);
    try {
      await closePr(detail.postId, { resultStatus });
      addToast(`PR이 ${resultStatus} 상태로 종료되었습니다.`, 'success');
      await loadDetail();
    } catch {
      addToast('PR 종료에 실패했습니다. 작성자만 종료할 수 있습니다.', 'error');
    } finally {
      setIsClosingPr(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-64 bg-gray-100 rounded-xl animate-pulse" />
        <Card className="h-72 animate-pulse bg-gray-50 border-gray-100">
          <div className="h-full" />
        </Card>
      </div>
    );
  }

  if (errorMessage || !detail) {
    return (
      <Card className="flex flex-col items-center gap-4 py-12 text-center">
        <h2 className="text-xl font-black text-gray-800">PR 상세 오류</h2>
        <p className="text-gray-500 font-medium">
          {errorMessage ?? '예상치 못한 오류가 발생했습니다.'}
        </p>
        <Button
          type="button"
          className="!w-auto px-6 py-2.5 text-sm"
          onClick={() => void loadDetail()}
        >
          다시 시도
        </Button>
      </Card>
    );
  }

  const isOpen = detail.status === 'OPEN';
  const canVote = detail.permissions?.canVote ?? isOpen;
  const canClose = detail.permissions?.canClose ?? isOpen;
  const voteDisabledReason = detail.permissions?.voteDisabledReason ?? '투표할 수 없습니다.';
  const agreeRatio =
    detail.totalVoteCount > 0 ? (detail.agreeCount / detail.totalVoteCount) * 100 : 0;
  const timelineEvents = buildTimelineEvents(detail);
  const contentSections = parseContentSections(detail.content);
  const primaryAttachment = detail.attachments[0] ?? null;
  const latestEventTime =
    detail.events && detail.events.length > 0
      ? detail.events[detail.events.length - 1].createdAt
      : detail.closedAt ?? detail.updatedAt;

  return (
    <div className="grid grid-cols-1 items-start gap-8 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="space-y-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <span
                className={`rounded-full border px-4 py-1 text-xs font-bold uppercase tracking-wider ${getStatusBadgeClass(detail.status)} shadow-sm`}
              >
                {normalizePrStatus(detail.status)}
              </span>
              <span className="text-xs font-bold text-text-subtle tracking-tight bg-surface-soft px-2.5 py-1 rounded-lg">PR #{detail.postId}</span>
            </div>
            <h1 className="text-3xl font-black leading-tight text-eel tracking-tight">{detail.title}</h1>
            <div className="flex items-center gap-3 text-sm font-semibold text-text-muted">
              <UserAvatar
                profileImageUrl={detail.authorProfileImageUrl}
                nickname={detail.authorNickname}
                className="h-9 w-9 border-2 border-white shadow-sm"
              />
              <div>
                <span className="text-eel">{detail.authorNickname}</span>
                <span className="mx-2 text-text-subtle opacity-40">|</span>
                <span className="text-text-subtle font-medium">작성 {formatAbsoluteDate(detail.createdAt)}</span>
                {detail.updatedAt !== detail.createdAt && (
                  <>
                    <span className="mx-2 text-text-subtle opacity-40">|</span>
                    <span className="text-text-subtle font-medium">수정 {formatRelativeTime(detail.updatedAt)}</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            fullWidth={false}
            className="!rounded-2xl !px-6 !py-3 !text-sm"
            onClick={() => navigate('/community/write?category=PR')}
          >
            글쓰기
          </Button>
        </div>

        <Card className="!p-0 overflow-hidden border-2 border-accent-soft/30 shadow-xl hover:shadow-2xl transition-all h-full flex flex-col">
          <div className="flex items-center justify-between gap-4 border-b border-light-gray bg-surface-muted/50 px-8 py-6">
            <div className="min-w-0">
              <p className="text-2xl font-black leading-tight text-eel truncate">{detail.itemName}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-accent animate-pulse" />
                <p className="text-xs font-bold text-text-muted tracking-tight">
                  최근 업데이트 {latestEventTime ? formatRelativeTime(latestEventTime) : '-'}
                </p>
              </div>
            </div>
            {detail.deadlineAt ? (
              <div className="shrink-0 flex flex-col items-end gap-1">
                <span className="text-[10px] uppercase font-black text-text-subtle mb-1">마감 기한</span>
                <span className="rounded-xl border border-danger-soft bg-danger-soft/30 px-3.5 py-1.5 text-xs font-bold text-danger">
                  {formatDateTime(detail.deadlineAt)}
                </span>
              </div>
            ) : null}
          </div>

          <div className="grid grid-cols-1 gap-4 border-b border-light-gray bg-gradient-to-br from-surface-muted via-blue-50/20 to-surface-muted px-8 py-6 md:grid-cols-3">
            <div className="rounded-2xl bg-white/80 p-5 shadow-sm ring-1 ring-light-gray">
              <p className="text-[11px] font-black text-text-subtle uppercase tracking-widest mb-1.5">요청 금액</p>
              <p className="text-2xl font-black text-eel tracking-tighter">
                {formatCurrency(detail.priceAmount)}
              </p>
            </div>
            <div className="rounded-2xl bg-success/5 p-5 shadow-sm border-2 border-success/20 group transition-all hover:bg-success/10 hover:border-success/40">
              <p className="text-[11px] font-black text-success uppercase tracking-widest mb-1.5 group-hover:scale-105 origin-left transition-transform">Approve</p>
              <div className="flex items-baseline gap-1">
                <p className="text-2xl font-black text-success tracking-tighter">
                  {detail.agreeCount}
                </p>
                <span className="text-[13px] font-bold text-success/60">표 참여</span>
              </div>
            </div>
            <div className="rounded-2xl bg-danger/5 p-5 shadow-sm border-2 border-danger/20 group transition-all hover:bg-danger/10 hover:border-danger/40">
              <p className="text-[11px] font-black text-danger uppercase tracking-widest mb-1.5 group-hover:scale-105 origin-left transition-transform">Reject</p>
              <div className="flex items-baseline gap-1">
                <p className="text-2xl font-black text-danger tracking-tighter">
                  {detail.disagreeCount}
                </p>
                <span className="text-[13px] font-bold text-danger/60">표 참여</span>
              </div>
            </div>
          </div>

          <div className="space-y-6 px-8 py-8 flex-1">
            {contentSections.map((section, idx) => (
              <div key={section.title} className={`space-y-3 ${idx !== contentSections.length - 1 ? 'pb-6 border-b border-dashed border-light-gray' : ''}`}>
                <h2 className="text-lg font-black text-eel flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-blue" />
                  {section.title}
                </h2>
                <div className="whitespace-pre-wrap text-[16px] leading-[1.7] text-gray-700 font-medium pl-3.5">
                  {section.body || '내용이 없습니다.'}
                </div>
              </div>
            ))}
            <div className="pt-4 flex items-center gap-2">
               <span className="text-xs font-black text-text-subtle uppercase tracking-tight">Category</span>
               <span className="text-sm font-bold text-eel bg-surface-soft px-3 py-1 rounded-full">{detail.category ?? '-'}</span>
            </div>
          </div>
        </Card>

        <div className="relative space-y-5 pl-12 pt-4">
          <div className="absolute bottom-6 left-5 top-6 w-[2px] bg-gradient-to-b from-primary-blue/30 via-light-gray to-accent/30" />
          {timelineEvents.map((event) => (
            <div key={event.id} className="relative group">
              <span
                className={`absolute -left-[35px] top-6 h-5 w-5 rounded-full border-[3px] border-white shadow-lg transition-transform group-hover:scale-125 z-10 ${getTimelineDotClass(event.type, event.decision)}`}
              />
              <Card className="!p-0 overflow-hidden border-light-gray shadow-sm group-hover:shadow-md transition-all group-hover:-translate-y-1">
                <div className="flex items-center justify-between gap-3 border-b border-light-gray bg-surface-muted px-6 py-4">
                  <div className="flex items-center gap-2.5">
                    <p className="text-sm font-black text-eel uppercase tracking-tight">
                      {event.title}
                    </p>
                    {event.actorLabel && (
                      <span className="rounded-lg bg-white px-2 py-0.5 text-[10px] font-bold text-text-muted border border-light-gray">
                        {event.actorLabel}
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] font-bold text-text-subtle uppercase">
                    {event.timeLabel}
                  </span>
                </div>
                <div className="space-y-2 px-6 py-5">
                  <p className="text-[13px] font-bold text-primary-blue/80 tracking-tight">{event.subTitle}</p>
                  <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-eel/80 font-medium">
                    {event.content}
                  </p>
                </div>
              </Card>
            </div>
          ))}
        </div>

        {detail.reviews && detail.reviews.length > 0 ? (
          <Card className="!p-0 overflow-hidden border-light-gray shadow-lg mt-8">
            <div className="flex items-center justify-between border-b border-light-gray bg-eel/[0.02] px-7 py-5">
              <h3 className="text-xl font-black text-eel tracking-tight">리뷰 코맨트</h3>
              <span className="text-xs font-bold text-text-subtle bg-white px-2.5 py-1 rounded-lg border border-light-gray">{detail.reviews.length}건</span>
            </div>
            <div className="divide-y divide-light-gray">
              {detail.reviews.map((review) => (
                <div key={review.reviewId} className="group px-7 py-6 hover:bg-surface-muted/30 transition-colors">
                  <div className="flex items-center gap-3 mb-3">
                    <UserAvatar
                      profileImageUrl={review.userProfileImageUrl}
                      nickname={review.userNickname}
                      className="h-8 w-8 shadow-sm"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-black text-eel">{review.userNickname ?? `사용자 #${review.userId}`}</span>
                        <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${review.decision === 'APPROVE' ? 'bg-success/10 text-success ring-1 ring-success/20' : 'bg-danger/10 text-danger ring-1 ring-danger/20'}`}>
                          {review.decision}
                        </span>
                      </div>
                      <p className="text-[11px] font-bold text-text-subtle mt-0.5">{formatRelativeTime(review.createdAt)}</p>
                    </div>
                  </div>
                  <div className="bg-white/50 rounded-2xl p-4 ring-1 ring-light-gray group-hover:ring-accent-soft transition-all">
                    <p className="text-[14px] leading-relaxed text-eel/80 font-medium">
                      {review.content && review.content.trim().length > 0
                        ? review.content
                        : '의견 없이 결정만 등록했습니다.'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {!isOpen && (
          <Card className="border-2 border-line-soft bg-surface-muted/30 py-12 text-center shadow-inner overflow-hidden relative">
            <div className="absolute inset-0 bg-pattern-dots opacity-20" />
            <div className="relative z-10">
              <h3 className="text-3xl font-black leading-tight text-eel tracking-tight">
                현재 종료된 요청구루 🐾
              </h3>
              <p className="mt-3 text-lg font-bold text-text-muted">
                최종 결과: <span className="text-accent uppercase">{detail.status}</span>
              </p>
            </div>
          </Card>
        )}
      </section>

      <aside className="space-y-6 xl:sticky xl:top-24 mt-4 xl:mt-0">
        <Card className="!p-0 overflow-hidden border-light-gray shadow-xl hover:shadow-2xl transition-all h-full">
          <div className="border-b border-light-gray bg-surface-muted/50 px-6 py-5">
            <h3 className="text-xl font-black text-eel tracking-tight">대상 상품</h3>
          </div>
          <div className="p-6 space-y-5">
            <div className="relative group overflow-hidden rounded-[24px] border border-light-gray shadow-inner bg-surface-soft">
              {primaryAttachment && primaryAttachment.contentType.startsWith('image/') ? (
                <img
                  src={primaryAttachment.fileUrl}
                  alt={primaryAttachment.fileName}
                  className="h-56 w-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
              ) : (
                <div className="flex h-56 w-full items-center justify-center text-text-subtle">
                  <svg className="w-12 h-12 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/40 to-transparent h-12" />
            </div>

            <div className="space-y-1">
              <p className="text-xl font-black text-eel leading-tight tracking-tight">{detail.itemName}</p>
              <p className="text-xs font-bold text-text-subtle uppercase tracking-widest">{detail.category || '기타'}</p>
            </div>

            <div className="flex items-baseline gap-1">
              <p className="text-4xl font-black text-eel tracking-tighter">
                {detail.priceAmount.toLocaleString()}
              </p>
              <span className="text-xl font-black text-eel/40">원</span>
            </div>

            {detail.purchaseUrl ? (
              <a
                href={detail.purchaseUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center gap-2 w-full rounded-2xl bg-brand-night py-4 text-center text-lg font-black text-white transition-all hover:bg-brand-night/90 hover:-translate-y-1 shadow-lg active:scale-95"
              >
                구매처 바로가기
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            ) : null}

            {detail.attachments.length > 0 ? (
              <div className="rounded-2xl border border-light-gray bg-surface-muted p-4">
                <p className="text-[11px] font-black text-text-subtle uppercase tracking-widest mb-3">첨부파일 {detail.attachments.length}</p>
                <div className="space-y-2">
                  {detail.attachments.map((attachment) => (
                    <a
                      key={attachment.attachmentId}
                      href={attachment.fileUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between gap-3 rounded-xl bg-white p-3 text-xs font-bold text-eel shadow-sm ring-1 ring-light-gray hover:ring-primary-blue hover:text-primary-blue transition-all"
                    >
                      <span className="truncate flex-1">{attachment.fileName}</span>
                      <span className="shrink-0 text-text-subtle font-medium">
                        {Math.max(1, Math.round(attachment.fileSize / 1024))}KB
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </Card>

        <Card className="!p-0 overflow-hidden border-light-gray shadow-xl">
          <div className="flex items-center justify-between border-b border-light-gray bg-surface-muted/50 px-6 py-5">
            <h3 className="text-xl font-black text-eel tracking-tight">투표 현황</h3>
            <span className="text-xs font-black text-text-subtle uppercase px-2 py-1 bg-white border border-light-gray rounded-lg">{detail.totalVoteCount} Members</span>
          </div>
          <div className="p-6 space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-[11px] font-black uppercase tracking-widest">
                <span className="text-success">Agree</span>
                <span className="text-danger">Reject</span>
              </div>
              <div className="h-5 flex overflow-hidden rounded-full bg-light-gray shadow-inner p-0.5 ring-1 ring-light-gray">
                {detail.totalVoteCount > 0 ? (
                  <>
                    {detail.agreeCount > 0 && (
                      <div
                        className="h-full bg-success transition-all duration-1000 flex items-center justify-center"
                        style={{ width: `${agreeRatio}%` }}
                      >
                        {agreeRatio > 15 && <span className="text-[9px] font-black text-white/80">{Math.round(agreeRatio)}%</span>}
                      </div>
                    )}
                    {detail.disagreeCount > 0 && (
                      <div
                        className="h-full bg-danger transition-all duration-1000 flex items-center justify-center border-l-2 border-white/20"
                        style={{ width: `${100 - agreeRatio}%` }}
                      >
                        {(100 - agreeRatio) > 15 && <span className="text-[9px] font-black text-white/80">{Math.round(100 - agreeRatio)}%</span>}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="h-full w-full bg-gray-200/50 flex items-center justify-center">
                    <span className="text-[9px] font-black text-text-subtle uppercase tracking-widest">Pending Votes</span>
                  </div>
                )}
              </div>
              <div className="flex justify-between items-end">
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-black text-success tracking-tighter">{detail.agreeCount}</span>
                  <span className="text-[11px] font-bold text-success/60">표</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-black text-danger tracking-tighter">{detail.disagreeCount}</span>
                  <span className="text-[11px] font-bold text-danger/60">표</span>
                </div>
              </div>
            </div>

            {canVote ? (
              <div className="space-y-4 pt-2 border-t border-light-gray">
                <textarea
                  className="min-h-[100px] w-full rounded-2xl border-2 border-light-gray bg-surface-muted/30 px-4 py-3 text-sm font-medium outline-none focus:border-accent-soft focus:bg-white focus:ring-4 focus:ring-accent-soft/20 transition-all resize-none"
                  placeholder="의견을 남겨주시면 큰 도움이 됩니다구루! (선택사항)"
                  value={voteOpinion}
                  onChange={(event) => setVoteOpinion(event.target.value)}
                  disabled={isSubmittingVote}
                  maxLength={1000}
                />
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    type="button"
                    className="!bg-none !bg-success !py-4 !rounded-2xl shadow-[0_4px_12px_rgba(21,128,61,0.2)] hover:shadow-[0_8px_16px_rgba(21,128,61,0.3)] transition-all"
                    onClick={() => void handleVote('AGREE')}
                    disabled={isSubmittingVote}
                  >
                    APPROVE
                  </Button>
                  <Button
                    type="button"
                    className="!bg-none !bg-danger !py-4 !rounded-2xl shadow-[0_4px_12px_rgba(225,29,72,0.2)] hover:shadow-[0_8px_16px_rgba(225,29,72,0.3)] transition-all"
                    onClick={() => void handleVote('DISAGREE')}
                    disabled={isSubmittingVote}
                  >
                    REJECT
                  </Button>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border-2 border-dashed border-light-gray bg-surface-muted/50 p-5 text-center">
                <p className="text-xs font-black text-text-subtle uppercase tracking-widest mb-1">Voting Disabled</p>
                <p className="text-sm font-bold text-text-muted leading-tight">{voteDisabledReason}</p>
              </div>
            )}
          </div>
        </Card>

        {canClose && (
          <Card className="!p-0 overflow-hidden border-light-gray shadow-xl bg-eel/5 ring-1 ring-eel/10">
            <div className="border-b border-light-gray/20 bg-eel/10 px-6 py-5">
              <h3 className="text-xl font-black text-eel tracking-tight">최종 상태 결정</h3>
            </div>
            <div className="p-6 space-y-5">
              <p className="text-[11px] font-bold text-text-muted leading-relaxed text-center px-4">
                이 구매 요청의 최종 수락 여부를 결정합니다. <br/>결정 후에는 내용을 수정하거나 투표를 받을 수 없습니다.
              </p>
              <div className="grid grid-cols-2 gap-3">
                <Button
                  type="button"
                  className="!bg-none !bg-success !py-4 !rounded-2xl shadow-[0_8px_20px_rgba(21,128,61,0.2)] hover:shadow-[0_12px_28px_rgba(21,128,61,0.3)] transition-all"
                  onClick={() => void handleClosePr('MERGED')}
                  disabled={isClosingPr}
                >
                  MERGE
                </Button>
                <Button
                  type="button"
                  className="!bg-none !bg-danger !py-4 !rounded-2xl shadow-[0_8px_20px_rgba(225,29,72,0.2)] hover:shadow-[0_12px_28px_rgba(225,29,72,0.3)] transition-all"
                  onClick={() => void handleClosePr('CLOSED')}
                  disabled={isClosingPr}
                >
                  CLOSE
                </Button>
              </div>
            </div>
          </Card>
        )}
      </aside>
    </div>
  );
};
