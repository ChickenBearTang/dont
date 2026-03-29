import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, Button } from '@/shared/components';
import { getPosts } from '../api/communityApi';
import { fetchMyPage } from '@/features/user/api/userApi';
import type { BoardCategory, GetPostListResponseDto, PostSummaryDto } from '../types';
import type { MyPageResponse } from '@/features/user/mypage/types';
import { UserAvatar } from '../components/UserAvatar';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

const PAGE_SIZE = 12;
const PR_STATUS_FILTERS = ['OPEN', 'MERGED', 'CLOSED'] as const;
const BOARD_STATUS_FILTERS = ['OPEN', 'CLOSED'] as const;

type PrStatusFilter = (typeof PR_STATUS_FILTERS)[number];
type BoardStatusFilter = (typeof BOARD_STATUS_FILTERS)[number];

const formatCurrency = (value: number | null | undefined): string => {
  if (value == null) return '-';
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);
};

const formatRelativeDate = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);

  if (diffMin < 1) return '방금';
  if (diffMin < 60) return `${diffMin}분 전`;
  if (diffHour < 24) return `${diffHour}시간 전`;

  const month = date.getMonth() + 1;
  const day = String(date.getDate()).padStart(2, '0');
  return `${month}.${day}`;
};

const formatDateTime = (dateStr: string | null | undefined) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('ko-KR', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getCategoryName = (category: BoardCategory | undefined) => {
  switch (category) {
    case 'FREE':
      return '자유';
    case 'COHORT':
      return '기수';
    case 'PR':
      return 'PR';
    case 'POLL':
      return '토론';
    case 'HOTDEAL':
      return '핫딜';
    default:
      return '전체';
  }
};

const getCategoryDot = (category: BoardCategory | undefined) => {
  switch (category) {
    case 'FREE':
      return 'bg-blue-400';
    case 'COHORT':
      return 'bg-violet-400';
    case 'PR':
      return 'bg-amber-400';
    case 'POLL':
      return 'bg-emerald-400';
    case 'HOTDEAL':
      return 'bg-rose-400';
    default:
      return 'bg-gray-300';
  }
};

const normalizePrStatus = (status: string | undefined) => status?.trim().toUpperCase() ?? 'OPEN';

const getStatusLabelWithEmoji = (status: string | undefined): string => {
  const normalized = normalizePrStatus(status);
  if (normalized === 'OPEN') return '📂 OPEN';
  if (normalized === 'MERGED') return '✔️ MERGED';
  if (normalized === 'CLOSED') return '🚫 CLOSED';
  return normalized;
};

const getPrStatusTone = (status: string | undefined) => {
  const normalizedStatus = normalizePrStatus(status);

  if (normalizedStatus === 'OPEN') return 'bg-blue-50 text-blue-700 border-blue-100';
  if (normalizedStatus === 'MERGED') return 'bg-emerald-50 text-emerald-700 border-emerald-100';
  if (normalizedStatus === 'CLOSED') return 'bg-rose-50 text-rose-700 border-rose-100';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

const getPollStatusTone = (isClosed: boolean) =>
  isClosed
    ? 'bg-rose-50 text-rose-700 border-rose-100'
    : 'bg-blue-50 text-blue-700 border-blue-100';

const getHotdealStatusTone = (isExpired: boolean | null | undefined) =>
  isExpired
    ? 'bg-rose-50 text-rose-700 border-rose-100'
    : 'bg-blue-50 text-blue-700 border-blue-100';

const getBoardFilterTone = (status: BoardStatusFilter) => {
  if (status === 'OPEN') {
    return 'bg-blue-50 text-blue-700 border-blue-100';
  }
  return 'bg-rose-50 text-rose-700 border-rose-100';
};

const BoardStatusFilterBar = ({
  selectedStatuses,
  onToggleStatus,
  onSelectAllStatuses,
}: {
  selectedStatuses: BoardStatusFilter[];
  onToggleStatus: (status: BoardStatusFilter) => void;
  onSelectAllStatuses: () => void;
}) => (
  <div className="flex flex-wrap items-center gap-2">
    <button
      type="button"
      onClick={onSelectAllStatuses}
      className={`rounded-full border px-3 py-1.5 text-[12px] font-bold transition ${selectedStatuses.length === BOARD_STATUS_FILTERS.length
          ? 'border-slate-300 bg-slate-900 text-white'
          : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300 hover:text-gray-700'
        }`}
    >
      전체
    </button>
    {BOARD_STATUS_FILTERS.map((status) => {
      const isSelected = selectedStatuses.includes(status);

      return (
        <button
          key={status}
          type="button"
          onClick={() => onToggleStatus(status)}
          className={`rounded-full border px-3 py-1.5 text-[12px] font-bold transition ${isSelected
              ? getBoardFilterTone(status)
              : 'border-gray-200 bg-white text-gray-400 hover:border-gray-300 hover:text-gray-600'
            }`}
        >
          {getStatusLabelWithEmoji(status)}
        </button>
      );
    })}
  </div>
);

const EmptyBoardState = ({ message }: { message: string }) => (
  <div className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 px-6 py-10 text-center">
    <p className="text-[14px] font-semibold text-gray-600">{message}</p>
    <p className="mt-1 text-[12px] text-gray-400">필터를 조정하거나 전체 보기를 눌러 보세요.</p>
  </div>
);

const AttachmentCountChip = ({ count }: { count: number }) =>
  count > 0 ? (
    <span className="rounded-full bg-amber-50 px-3 py-1 text-[12px] font-semibold text-amber-700">
      첨부 {count}
    </span>
  ) : null;

const AuthorMeta = ({ post }: { post: PostSummaryDto }) => (
  <div className="flex w-full items-center justify-start gap-2 min-w-0">
    <UserAvatar
      profileImageUrl={post.authorProfileImageUrl}
      nickname={post.authorNickname}
      className="h-7 w-7 shrink-0 text-[12px]"
    />
    <span className="truncate">{post.authorNickname || '작성자 없음'}</span>
  </div>
);

const HotdealBoardList = ({
  posts,
  loading,
  onOpenPost,
  selectedStatuses,
  onToggleStatus,
  onSelectAllStatuses,
}: {
  posts: PostSummaryDto[];
  loading: boolean;
  onOpenPost: (post: PostSummaryDto) => void;
  selectedStatuses: BoardStatusFilter[];
  onToggleStatus: (status: BoardStatusFilter) => void;
  onSelectAllStatuses: () => void;
}) => {
  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center">
        <div className="w-7 h-7 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
        <span className="mt-3 text-[12px] font-medium text-gray-300">불러오는 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <BoardStatusFilterBar
        selectedStatuses={selectedStatuses}
        onToggleStatus={onToggleStatus}
        onSelectAllStatuses={onSelectAllStatuses}
      />

      {posts.length === 0 ? (
        <EmptyBoardState message="선택한 상태에 해당하는 핫딜이 없습니다" />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {posts.map((post) => {
            const hotdeal = post.extraSummary?.hotdeal;
            const originalPrice = hotdeal?.originalPriceAmount ?? 0;
            const dealPrice = hotdeal?.dealPriceAmount ?? 0;
            const discountRate =
              originalPrice > 0 && dealPrice > 0
                ? Math.max(0, Math.round(((originalPrice - dealPrice) / originalPrice) * 100))
                : null;

            return (
              <button
                key={post.postId}
                type="button"
                onClick={() => onOpenPost(post)}
                className="text-left rounded-2xl border border-gray-100 bg-white px-5 py-5 transition hover:border-rose-200 hover:bg-rose-50/30"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-2 text-[12px] font-semibold text-rose-600">
                        <span className="w-2 h-2 rounded-full bg-rose-400" />
                        HOTDEAL
                      </span>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-[11px] font-bold ${getHotdealStatusTone(
                          hotdeal?.isExpired
                        )}`}
                      >
                        {getStatusLabelWithEmoji(hotdeal?.isExpired ? 'CLOSED' : 'OPEN')}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-[19px] font-bold text-gray-900 tracking-[-0.02em]">
                        {post.title}
                      </h3>
                      <p className="mt-1 text-[13px] font-medium text-gray-500">
                        {hotdeal?.storeName || '판매처 미정'}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3 min-w-[220px]">
                    <p className="text-[11px] font-semibold text-gray-400">딜 가격</p>
                    <p className="mt-1 text-[22px] font-black leading-none text-gray-900">
                      {formatCurrency(hotdeal?.dealPriceAmount)}
                    </p>
                    <div className="mt-2 flex items-center gap-2 text-[12px] font-semibold">
                      {hotdeal?.originalPriceAmount ? (
                        <span className="text-gray-400 line-through">
                          {formatCurrency(hotdeal.originalPriceAmount)}
                        </span>
                      ) : null}
                      {discountRate != null ? (
                        <span className="text-rose-600">{discountRate}% 할인</span>
                      ) : null}
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-rose-50 px-3 py-1 text-[12px] font-semibold text-rose-700">
                    종료 {formatDateTime(hotdeal?.expiredAt)}
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[12px] font-semibold text-slate-600">
                    좋아요 {post.likeCount || 0}
                  </span>
                  <AttachmentCountChip count={post.attachmentCount} />
                  {post.commentCount > 0 ? (
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-[12px] font-semibold text-blue-600">
                      댓글 {post.commentCount}
                    </span>
                  ) : null}
                </div>

                <div className="mt-4 flex items-center justify-between text-[12px] font-medium text-gray-400">
                  <AuthorMeta post={post} />
                  <span className="whitespace-nowrap shrink-0">{formatRelativeDate(post.createdAt)}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

const PollBoardList = ({
  posts,
  loading,
  onOpenPost,
  selectedStatuses,
  onToggleStatus,
  onSelectAllStatuses,
}: {
  posts: PostSummaryDto[];
  loading: boolean;
  onOpenPost: (post: PostSummaryDto) => void;
  selectedStatuses: BoardStatusFilter[];
  onToggleStatus: (status: BoardStatusFilter) => void;
  onSelectAllStatuses: () => void;
}) => {
  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center">
        <div className="w-7 h-7 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
        <span className="mt-3 text-[12px] font-medium text-gray-300">불러오는 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <BoardStatusFilterBar
        selectedStatuses={selectedStatuses}
        onToggleStatus={onToggleStatus}
        onSelectAllStatuses={onSelectAllStatuses}
      />

      {posts.length === 0 ? (
        <EmptyBoardState message="선택한 상태에 해당하는 토론이 없습니다" />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {posts.map((post) => {
            const poll = post.extraSummary?.poll;
            const totalVotes = poll?.totalVoteCount ?? 0;
            const optionARate =
              totalVotes > 0 ? Math.round(((poll?.optionACount ?? 0) / totalVotes) * 100) : 0;
            const optionBRate =
              totalVotes > 0 ? Math.round(((poll?.optionBCount ?? 0) / totalVotes) * 100) : 0;

            return (
              <button
                key={post.postId}
                type="button"
                onClick={() => onOpenPost(post)}
                className="text-left rounded-2xl border border-gray-100 bg-white px-5 py-5 transition hover:border-emerald-200 hover:bg-emerald-50/30"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-2 text-[12px] font-semibold text-emerald-600">
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                        POLL
                      </span>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-[11px] font-bold ${getPollStatusTone(
                          poll?.isClosed ?? false
                        )}`}
                      >
                        {getStatusLabelWithEmoji(poll?.isClosed ? 'CLOSED' : 'OPEN')}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-[19px] font-bold text-gray-900 tracking-[-0.02em]">
                        {post.title}
                      </h3>
                      <p className="mt-1 text-[14px] font-semibold text-gray-700">
                        {poll?.question ?? '질문 없음'}
                      </p>
                    </div>
                  </div>

                  <div className="min-w-[220px] rounded-2xl border border-gray-100 bg-gray-50 px-4 py-4">
                    <p className="text-[11px] font-semibold text-gray-400">투표 현황</p>
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between gap-3 text-[12px] font-medium text-gray-600">
                        <span className="truncate">{poll?.optionA ?? '선택지 A'}</span>
                        <span>{optionARate}%</span>
                      </div>
                      <div className="h-2 rounded-full bg-white">
                        <div
                          className="h-2 rounded-full bg-emerald-400"
                          style={{ width: `${optionARate}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between gap-3 text-[12px] font-medium text-gray-600">
                        <span className="truncate">{poll?.optionB ?? '선택지 B'}</span>
                        <span>{optionBRate}%</span>
                      </div>
                      <div className="h-2 rounded-full bg-white">
                        <div
                          className="h-2 rounded-full bg-teal-600"
                          style={{ width: `${optionBRate}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-emerald-50 px-3 py-1 text-[12px] font-semibold text-emerald-700">
                    참여 {totalVotes}명
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[12px] font-semibold text-slate-600">
                    마감 {formatDateTime(poll?.deadlineAt)}
                  </span>
                  <span className="rounded-full bg-rose-50 px-3 py-1 text-[12px] font-semibold text-rose-500">
                    좋아요 {post.likeCount || 0}
                  </span>
                  <AttachmentCountChip count={post.attachmentCount} />
                  {post.commentCount > 0 ? (
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-[12px] font-semibold text-blue-600">
                      댓글 {post.commentCount}
                    </span>
                  ) : null}
                </div>

                <div className="mt-4 flex items-center justify-between text-[12px] font-medium text-gray-400">
                  <AuthorMeta post={post} />
                  <span className="whitespace-nowrap shrink-0">{formatRelativeDate(post.createdAt)}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

const PrBoardList = ({
  posts,
  loading,
  onOpenPost,
  selectedStatuses,
  onToggleStatus,
  onSelectAllStatuses,
}: {
  posts: PostSummaryDto[];
  loading: boolean;
  onOpenPost: (post: PostSummaryDto) => void;
  selectedStatuses: PrStatusFilter[];
  onToggleStatus: (status: PrStatusFilter) => void;
  onSelectAllStatuses: () => void;
}) => {
  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center">
        <div className="w-7 h-7 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
        <span className="mt-3 text-[12px] font-medium text-gray-300">불러오는 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onSelectAllStatuses}
          className={`rounded-full border px-3 py-1.5 text-[12px] font-bold transition ${selectedStatuses.length === PR_STATUS_FILTERS.length
              ? 'border-slate-300 bg-slate-900 text-white'
              : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300 hover:text-gray-700'
            }`}
        >
          전체
        </button>
        {PR_STATUS_FILTERS.map((status) => {
          const isSelected = selectedStatuses.includes(status);

          return (
            <button
              key={status}
              type="button"
              onClick={() => onToggleStatus(status)}
              className={`rounded-full border px-3 py-1.5 text-[12px] font-bold transition ${isSelected
                  ? getPrStatusTone(status)
                  : 'border-gray-200 bg-white text-gray-400 hover:border-gray-300 hover:text-gray-600'
                }`}
            >
              {getStatusLabelWithEmoji(status)}
            </button>
          );
        })}
      </div>

      {posts.length === 0 ? (
        <EmptyBoardState message="선택한 상태에 해당하는 PR이 없습니다" />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {posts.map((post) => {
            const pr = post.extraSummary?.pr;
            return (
              <button
                key={post.postId}
                type="button"
                onClick={() => onOpenPost(post)}
                className="text-left rounded-2xl border border-gray-100 bg-white px-5 py-5 transition hover:border-amber-200 hover:bg-amber-50/30"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-2 text-[12px] font-semibold text-amber-600">
                        <span className="w-2 h-2 rounded-full bg-amber-400" />
                        PR
                      </span>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-[11px] font-bold ${getPrStatusTone(
                          pr?.resultStatus ?? pr?.status
                        )}`}
                      >
                        {getStatusLabelWithEmoji(pr?.resultStatus ?? pr?.status)}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-[19px] font-bold text-gray-900 tracking-[-0.02em]">
                        {post.title}
                      </h3>
                      <p className="mt-1 text-[13px] font-medium text-gray-500">
                        {pr?.itemName ?? '상품명 없음'}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3 min-w-[180px]">
                    <p className="text-[11px] font-semibold text-gray-400">요청 금액</p>
                    <p className="mt-1 text-[22px] font-black leading-none text-gray-900">
                      {formatCurrency(pr?.priceAmount)}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-amber-50 px-3 py-1 text-[12px] font-semibold text-amber-700">
                    투표 {pr?.totalVoteCount ?? 0}명
                  </span>
                  {pr?.deadlineAt ? (
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-[12px] font-semibold text-slate-600">
                      마감 {formatRelativeDate(pr.deadlineAt)}
                    </span>
                  ) : null}
                  <span className="rounded-full bg-rose-50 px-3 py-1 text-[12px] font-semibold text-rose-500">
                    좋아요 {post.likeCount || 0}
                  </span>
                  <AttachmentCountChip count={post.attachmentCount} />
                  {post.commentCount > 0 ? (
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-[12px] font-semibold text-blue-600">
                      댓글 {post.commentCount}
                    </span>
                  ) : null}
                </div>

                <div className="mt-4 flex items-center justify-between text-[12px] font-medium text-gray-400">
                  <AuthorMeta post={post} />
                  <span className="whitespace-nowrap shrink-0">{formatRelativeDate(post.createdAt)}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export const CommunityPage = () => {
  const { user } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const { data: myPageData } = useQuery<MyPageResponse>({
    queryKey: ['myPage'],
    queryFn: () => fetchMyPage().then((res) => res.data),
    enabled: !!user,
  });
  const cohortNo = myPageData?.cohortGenerationNo ?? user?.cohortId;

  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const category = searchParams.get('category') as BoardCategory | null;
  const pageParam = Number(searchParams.get('page'));
  const currentPage = Number.isInteger(pageParam) && pageParam >= 1 ? pageParam : 1;
  const urlSearch = searchParams.get('search') || '';

  const [posts, setPosts] = useState<PostSummaryDto[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [pageInfo, setPageInfo] = useState<GetPostListResponseDto | null>(null);
  const [searchInput, setSearchInput] = useState(urlSearch);
  const [keyword, setKeyword] = useState(urlSearch);
  const [selectedPrStatuses, setSelectedPrStatuses] = useState<PrStatusFilter[]>([
    'OPEN',
    'MERGED',
    'CLOSED',
  ]);
  const [selectedPollStatuses, setSelectedPollStatuses] = useState<BoardStatusFilter[]>([
    'OPEN',
    'CLOSED',
  ]);
  const [selectedHotdealStatuses, setSelectedHotdealStatuses] = useState<BoardStatusFilter[]>([
    'OPEN',
    'CLOSED',
  ]);

  useEffect(() => {
    setSearchInput(urlSearch);
    setKeyword(urlSearch);
  }, [urlSearch]);

  useEffect(() => {
    const fetchPosts = async () => {
      setLoading(true);

      try {
        const res = await getPosts(category, keyword || undefined, currentPage - 1, PAGE_SIZE);

        if (res.data) {
          setPosts(res.data.content ?? []);
          setPageInfo(res.data);
        } else {
          setPosts([]);
          setPageInfo(null);
        }
      } catch (error) {
        console.error('Failed to fetch posts:', error);
        setPosts([]);
        setPageInfo(null);
      } finally {
        setLoading(false);
      }
    };

    void fetchPosts();
  }, [category, currentPage, keyword]);

  const isPrBoard = category === 'PR';
  const isPollBoard = category === 'POLL';
  const isHotdealBoard = category === 'HOTDEAL';
  const totalPages = pageInfo?.totalPages ?? 0;
  const totalElements = pageInfo?.totalElements ?? 0;

  const getPostDetailPath = (post: PostSummaryDto) => {
    if (post.category === 'PR') {
      return `/community/pr/${post.postId}`;
    }
    return `/community/${post.postId}`;
  };

  const getWritePath = () => (category ? `/community/write?category=${category}` : '/community/write');

  const filteredPosts = useMemo(() => {
    const searchedPosts = !keyword
      ? posts
      : posts.filter((post) => post.title.toLowerCase().includes(keyword.toLowerCase()));

    if (isPrBoard) {
      return searchedPosts.filter((post) => {
        const prStatus = normalizePrStatus(
          post.extraSummary?.pr?.resultStatus ?? post.extraSummary?.pr?.status
        );
        return selectedPrStatuses.includes(prStatus as PrStatusFilter);
      });
    }

    if (isPollBoard) {
      return searchedPosts.filter((post) => {
        const status: BoardStatusFilter = post.extraSummary?.poll?.isClosed ? 'CLOSED' : 'OPEN';
        return selectedPollStatuses.includes(status);
      });
    }

    if (isHotdealBoard) {
      return searchedPosts.filter((post) => {
        const status: BoardStatusFilter = post.extraSummary?.hotdeal?.isExpired ? 'CLOSED' : 'OPEN';
        return selectedHotdealStatuses.includes(status);
      });
    }

    return searchedPosts;
  }, [
    isHotdealBoard,
    isPollBoard,
    isPrBoard,
    keyword,
    posts,
    selectedHotdealStatuses,
    selectedPollStatuses,
    selectedPrStatuses,
  ]);

  const listCount =
    isPrBoard || isPollBoard || isHotdealBoard
      ? filteredPosts.length
      : keyword
        ? filteredPosts.length
        : totalElements;

  const visiblePageNumbers = useMemo(() => {
    if (totalPages <= 0) return [];

    const maxButtons = 5;
    const half = Math.floor(maxButtons / 2);
    let start = Math.max(1, currentPage - half);
    const end = Math.min(totalPages, start + maxButtons - 1);

    if (end - start + 1 < maxButtons) {
      start = Math.max(1, end - maxButtons + 1);
    }

    return Array.from({ length: end - start + 1 }, (_, idx) => start + idx);
  }, [currentPage, totalPages]);

  const categoryTitle = keyword
    ? `'${keyword}' 검색 결과`
    : category
      ? category === 'COHORT' && cohortNo
        ? `${cohortNo}기 게시판`
        : `${getCategoryName(category)} 게시판`
      : '전체 게시판';

  const categoryDescription = keyword
    ? `${totalElements}개의 게시글을 찾았습니다.`
    : category === 'PR'
      ? '구매 요청을 올리고 다른 사용자의 의견을 받아보세요.'
      : category === 'COHORT'
        ? `${cohortNo ?? ''}기 동기들과 자유롭게 소통하고 정보를 나누어보세요.`
      : category === 'POLL'
        ? '찬반이 갈리는 주제를 올리고 기한 안에 의견을 모아보세요.'
        : category === 'HOTDEAL'
          ? '딜 가격과 판매처, 종료 시각을 빠르게 공유해 보세요.'
          : '우리만의 소식을 나누고 함께 소통해 보세요.';

  const moveToListPage = (targetPage: number) => {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (targetPage > 1) params.set('page', String(targetPage));
    if (keyword) params.set('search', keyword);
    const queryString = params.toString();
    navigate(queryString ? `/community?${queryString}` : '/community');
  };

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = searchInput.trim();
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (trimmed) params.set('search', trimmed);
    const queryString = params.toString();
    navigate(queryString ? `/community?${queryString}` : '/community');
  };

  const toggleBoardStatus = (
    status: BoardStatusFilter,
    setSelectedStatuses: React.Dispatch<React.SetStateAction<BoardStatusFilter[]>>
  ) => {
    setSelectedStatuses((prev) => {
      if (prev.includes(status)) {
        if (prev.length === 1) return prev;
        return prev.filter((value) => value !== status);
      }
      return [...prev, status];
    });
  };

  const togglePrStatus = (status: PrStatusFilter) => {
    setSelectedPrStatuses((prev) => {
      if (prev.includes(status)) {
        if (prev.length === 1) return prev;
        return prev.filter((value) => value !== status);
      }
      return [...prev, status];
    });
  };

  return (
    <Card className="!p-0 flex flex-col min-h-[600px] overflow-hidden">
      <div className="px-7 pt-7 pb-5 flex justify-between items-start relative z-10 w-full">
        <div>
          <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">{categoryTitle}</h1>
          <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
            {categoryDescription}
          </p>
        </div>

        <div className="flex gap-2.5 items-center shrink-0">
          <form onSubmit={handleSearch} className="relative">
            <button
              type="submit"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-300 hover:text-gray-500 transition-colors"
            >
              <svg className="w-[15px] h-[15px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" strokeLinecap="round" />
              </svg>
            </button>
            <input
              type="text"
              placeholder="검색"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              className="bg-gray-50 border border-gray-100 text-[13px] rounded-xl pl-10 pr-4 h-[44px] w-[210px] outline-none focus:border-gray-200 focus:bg-white transition-all font-semibold text-gray-600 placeholder:text-gray-300"
            />
          </form>

          <Button
            type="button"
            onClick={() => navigate(getWritePath())}
            fullWidth={false}
            className="!inline-flex items-center gap-2 rounded-xl border-0 !bg-blue-600 px-6 h-[44px] text-[14px] font-black text-white shadow-md transition hover:!bg-blue-700 hover:-translate-y-0.5 active:scale-95 focus:outline-none"
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
            <span>글쓰기</span>
          </Button>
        </div>
      </div>

      <div className="mx-7 border-t border-gray-100" />

      <div className="px-7 pb-6 flex-1 flex flex-col relative z-10">
        <div className="flex items-center justify-between py-3">
          <div className="text-[12px] text-gray-400 font-medium">
            총 <span className="font-bold text-gray-700">{listCount}</span>개
          </div>
          <div className="text-[12px] text-gray-400 font-medium">
            페이지 <span className="font-bold text-gray-700">{currentPage}</span>
            {totalPages > 0 ? ` / ${totalPages}` : ''}
          </div>
        </div>

        {isPrBoard ? (
          <PrBoardList
            posts={filteredPosts}
            loading={loading}
            onOpenPost={(post) => navigate(getPostDetailPath(post))}
            selectedStatuses={selectedPrStatuses}
            onToggleStatus={togglePrStatus}
            onSelectAllStatuses={() => setSelectedPrStatuses([...PR_STATUS_FILTERS])}
          />
        ) : isPollBoard ? (
          <PollBoardList
            posts={filteredPosts}
            loading={loading}
            onOpenPost={(post) => navigate(getPostDetailPath(post))}
            selectedStatuses={selectedPollStatuses}
            onToggleStatus={(status) => toggleBoardStatus(status, setSelectedPollStatuses)}
            onSelectAllStatuses={() => setSelectedPollStatuses([...BOARD_STATUS_FILTERS])}
          />
        ) : isHotdealBoard ? (
          <HotdealBoardList
            posts={filteredPosts}
            loading={loading}
            onOpenPost={(post) => navigate(getPostDetailPath(post))}
            selectedStatuses={selectedHotdealStatuses}
            onToggleStatus={(status) => toggleBoardStatus(status, setSelectedHotdealStatuses)}
            onSelectAllStatuses={() => setSelectedHotdealStatuses([...BOARD_STATUS_FILTERS])}
          />
        ) : (
          <>
            <div className="grid grid-cols-12 gap-3 py-3 text-[12px] font-semibold text-gray-300 uppercase tracking-wider items-center border-t border-gray-50">
              <div className="col-span-1">분류</div>
              <div className="col-span-7">제목</div>
              <div className="col-span-2 text-center">작성자</div>
              <div className="col-span-2 text-right pr-1">날짜</div>
            </div>

            <div className="flex flex-col flex-1">
              {loading ? (
                <div className="py-28 flex flex-col items-center justify-center">
                  <div className="w-6 h-6 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
                  <span className="text-[12px] text-gray-300 mt-3 font-medium">불러오는 중...</span>
                </div>
              ) : filteredPosts.length === 0 ? (
                <div className="py-28 flex flex-col items-center justify-center">
                  <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center mb-3">
                    <svg className="w-5 h-5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path
                        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                  <p className="font-semibold text-gray-400 text-[13px]">등록된 게시물이 없습니다</p>
                  <p className="text-[12px] text-gray-300 mt-1">첫 글을 작성해 보세요.</p>
                </div>
              ) : (
                filteredPosts.map((post, idx) => (
                  <div
                    key={post.postId}
                    onClick={() => navigate(getPostDetailPath(post))}
                    className={`grid grid-cols-12 gap-3 py-3.5 text-[13.5px] items-center hover:bg-gray-50/60 transition-colors cursor-pointer group ${idx !== filteredPosts.length - 1 ? 'border-b border-gray-50' : ''
                      }`}
                  >
                    <div className="col-span-1 flex items-center gap-0">
                      <span className={`w-1.5 h-1.5 rounded-full ${getCategoryDot(post.category)} flex-shrink-0`} />
                      <span className="text-[12px] text-gray-400 font-medium ml-1.5 hidden lg:inline">
                        {getCategoryName(post.category)}
                      </span>
                    </div>

                    <div className="col-span-7 flex items-center gap-2 min-w-0">
                      <span
                        className={`truncate font-medium ${post.status === 'BLINDED' ? 'text-gray-400 italic' : 'text-gray-800 group-hover:text-gray-900'
                          }`}
                      >
                        {post.status === 'BLINDED' ? '신고 처리된 게시물입니다.' : post.title}
                      </span>

                      {post.commentCount > 0 && (
                        <span className="text-[12px] font-semibold text-blue-500 shrink-0">
                          [{post.commentCount}]
                        </span>
                      )}
                      {post.attachmentCount > 0 && (
                        <span className="text-[12px] font-semibold text-amber-600 shrink-0">
                          [첨부 {post.attachmentCount}]
                        </span>
                      )}

                      <div className="flex items-center gap-0.5 ml-1 shrink-0 text-rose-400">
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001z" />
                        </svg>
                        <span className="text-[11.5px] font-bold">{post.likeCount || 0}</span>
                      </div>
                    </div>

                    <div className="col-span-2 flex justify-start text-gray-500 text-[13px] font-medium min-w-0">
                      <AuthorMeta post={post} />
                    </div>

                    <div className="col-span-2 text-right text-gray-400 text-[12px] font-medium whitespace-nowrap">
                      {formatRelativeDate(post.createdAt)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {!loading && totalPages > 1 && (
          <div className="mt-8 flex items-center justify-center gap-1.5">
            <button
              type="button"
              onClick={() => moveToListPage(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-2 rounded-lg border border-line-soft text-[13px] font-bold text-text-muted disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-soft transition-colors"
            >
              이전
            </button>

            {visiblePageNumbers.map((pageNumber) => (
              <button
                key={pageNumber}
                type="button"
                onClick={() => moveToListPage(pageNumber)}
                className={`min-w-[36px] h-[36px] rounded-lg text-[13px] font-semibold transition ${pageNumber === currentPage ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-50'
                  }`}
              >
                {pageNumber}
              </button>
            ))}

            <button
              type="button"
              onClick={() => moveToListPage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-2 rounded-lg border border-line-soft text-[13px] font-bold text-text-muted disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-soft transition-colors"
            >
              다음
            </button>
          </div>
        )}
      </div>
    </Card>
  );
};
