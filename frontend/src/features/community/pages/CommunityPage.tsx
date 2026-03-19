import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getPosts } from '../api/communityApi';
import type { BoardCategory, GetPostListResponseDto, PostSummaryDto } from '../types';

const PAGE_SIZE = 12;
type PrStatusFilter = 'ALL' | 'OPEN' | 'MERGED' | 'CLOSED';
type PrStatusValue = 'OPEN' | 'MERGED' | 'CLOSED' | 'UNKNOWN';

const CATEGORY_LABEL: Record<string, string> = {
  FREE: '자유',
  COHORT: '기수',
  PR: 'PR',
  POLL: '투표',
  HOTDEAL: '핫딜',
};

const PR_FILTERS: PrStatusFilter[] = ['ALL', 'OPEN', 'MERGED', 'CLOSED'];

const getCategoryName = (category: BoardCategory | null): string => {
  if (!category) return '전체';
  return CATEGORY_LABEL[category] ?? '전체';
};

const getCategoryDot = (category: BoardCategory | undefined) => {
  switch (category) {
    case 'FREE':
      return 'bg-blue-400';
    case 'COHORT':
      return 'bg-violet-400';
    case 'PR':
      return 'bg-emerald-400';
    case 'POLL':
      return 'bg-cyan-400';
    case 'HOTDEAL':
      return 'bg-rose-400';
    default:
      return 'bg-gray-300';
  }
};

const getPrStatus = (post: PostSummaryDto): PrStatusValue => {
  const status = post.extraSummary?.pr?.status;
  if (status === 'OPEN' || status === 'MERGED' || status === 'CLOSED') return status;
  return 'UNKNOWN';
};

const getPrStatusBadgeClass = (status: PrStatusValue): string => {
  if (status === 'OPEN') return 'bg-[#1e3a8a] text-[#dbeafe] border border-[#3b82f6]';
  if (status === 'MERGED') return 'bg-[#14532d] text-[#dcfce7] border border-[#22c55e]';
  if (status === 'CLOSED') return 'bg-[#374151] text-[#f3f4f6] border border-[#6b7280]';
  return 'bg-[#3f3f46] text-[#fafafa] border border-[#71717a]';
};

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);

  if (diffMin < 1) return '방금';
  if (diffMin < 60) return `${diffMin}분 전`;
  if (diffHour < 24) return `${diffHour}시간 전`;

  return date.toLocaleDateString('ko-KR', {
    month: 'numeric',
    day: 'numeric',
  });
};

const formatPrGroupDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

const buildPrGroups = (posts: PostSummaryDto[]) => {
  const groups = new Map<string, PostSummaryDto[]>();
  posts.forEach((post) => {
    const key = formatPrGroupDate(post.createdAt);
    const current = groups.get(key) ?? [];
    current.push(post);
    groups.set(key, current);
  });
  return Array.from(groups.entries()).map(([dateLabel, items]) => ({ dateLabel, items }));
};

export const CommunityPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const category = searchParams.get('category') as BoardCategory | null;
  const statusParam = searchParams.get('status');
  const selectedPrStatus: PrStatusFilter =
    statusParam === 'OPEN' || statusParam === 'MERGED' || statusParam === 'CLOSED'
      ? statusParam
      : 'ALL';
  const pageParam = Number(searchParams.get('page'));
  const currentPage = Number.isInteger(pageParam) && pageParam >= 1 ? pageParam : 1;

  const [posts, setPosts] = useState<PostSummaryDto[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [pageInfo, setPageInfo] = useState<GetPostListResponseDto | null>(null);

  useEffect(() => {
    const fetchPosts = async () => {
      setLoading(true);
      try {
        const response = await getPosts(category, undefined, currentPage - 1, PAGE_SIZE);
        setPosts(response.data?.content ?? []);
        setPageInfo(response.data ?? null);
      } catch {
        setPosts([]);
        setPageInfo(null);
      } finally {
        setLoading(false);
      }
    };

    void fetchPosts();
  }, [category, currentPage]);

  const moveToListPage = (targetPage: number) => {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (category === 'PR' && selectedPrStatus !== 'ALL') params.set('status', selectedPrStatus);
    if (targetPage > 1) params.set('page', String(targetPage));
    const queryString = params.toString();
    navigate(queryString ? `/community?${queryString}` : '/community');
  };

  const movePrStatus = (status: PrStatusFilter) => {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (status !== 'ALL') params.set('status', status);
    navigate(`/community?${params.toString()}`);
  };

  const isPrCategory = category === 'PR';
  const prStatusCounts = useMemo(
    () => ({
      ALL: posts.length,
      OPEN: posts.filter((post) => getPrStatus(post) === 'OPEN').length,
      MERGED: posts.filter((post) => getPrStatus(post) === 'MERGED').length,
      CLOSED: posts.filter((post) => getPrStatus(post) === 'CLOSED').length,
    }),
    [posts]
  );
  const filteredPrPosts = useMemo(
    () =>
      posts.filter((post) => {
        if (selectedPrStatus === 'ALL') return true;
        return getPrStatus(post) === selectedPrStatus;
      }),
    [posts, selectedPrStatus]
  );
  const prGroups = useMemo(() => buildPrGroups(filteredPrPosts), [filteredPrPosts]);

  const categoryTitle = `${getCategoryName(category)} 게시판`;
  const cohortGenerationNo = category === 'COHORT' && posts.length > 0 ? posts[0].generationNo : null;
  const categoryDescription =
    category === 'COHORT'
      ? cohortGenerationNo
        ? `${cohortGenerationNo}기 게시판입니다. 자유롭게 이야기를 남겨보세요.`
        : '기수 게시판입니다. 자유롭게 이야기를 남겨보세요.'
      : '우리만의 지식을 나누고 빠르게 소통해보세요.';

  const totalPages = pageInfo?.totalPages ?? 0;
  const totalElements = pageInfo?.totalElements ?? 0;
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

  const handleWrite = () => {
    if (isPrCategory) {
      navigate('/community/pr/new');
      return;
    }
    navigate(category ? `/community/write?category=${category}` : '/community/write');
  };

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
      <div className="px-7 pt-7 pb-5 flex justify-between items-start">
        <div>
          <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">{categoryTitle}</h1>
          <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">{categoryDescription}</p>
        </div>

        <button
          type="button"
          onClick={handleWrite}
          className="inline-flex items-center gap-2 rounded-xl border border-blue-600 bg-blue-600 px-4 py-2.5 text-[14px] font-bold text-white shadow-sm transition hover:border-blue-700 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
        >
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 5v14M5 12h14" strokeLinecap="round" />
          </svg>
          <span>{isPrCategory ? 'PR 작성' : '글쓰기'}</span>
        </button>
      </div>

      <div className="mx-7 border-t border-gray-100" />

      <div className="px-7 pb-6 flex-1 flex flex-col">
        <div className="flex items-center justify-between py-3">
          <div className="text-[12px] text-gray-400 font-medium">
            총 <span className="font-bold text-gray-700">{totalElements}</span>개
          </div>
          <div className="text-[12px] text-gray-400 font-medium">
            페이지 <span className="font-bold text-gray-700">{currentPage}</span>
            {totalPages > 0 ? ` / ${totalPages}` : ''}
          </div>
        </div>

        {isPrCategory ? (
          <div className="rounded-2xl border border-[#273449] bg-[#0b1220] px-5 py-5 text-[#f8fbff]">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              {PR_FILTERS.map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => movePrStatus(status)}
                  className={`rounded-full px-3.5 py-1.5 text-xs font-bold transition ${
                    selectedPrStatus === status
                      ? 'bg-[#f8fafc] text-[#0f172a]'
                      : 'bg-[#1e293b] text-[#dbeafe] hover:bg-[#334155]'
                  }`}
                >
                  {status} ({prStatusCounts[status]})
                </button>
              ))}
            </div>

            {loading ? (
              <div className="py-20 flex flex-col items-center justify-center">
                <div className="w-6 h-6 border-2 border-slate-700 border-t-slate-200 rounded-full animate-spin" />
                <span className="text-[12px] text-[#bfd2ee] mt-3 font-medium">불러오는 중...</span>
              </div>
            ) : filteredPrPosts.length === 0 ? (
              <div className="py-20 text-center text-[#bfd2ee] text-sm font-medium">선택한 상태의 PR이 없습니다.</div>
            ) : (
              <div className="space-y-5">
                {prGroups.map((group) => (
                  <section key={group.dateLabel} className="space-y-2.5">
                    <p className="text-sm text-[#b8c7df] font-semibold">{group.dateLabel}</p>
                    <div className="relative pl-7 space-y-2">
                      <div className="absolute left-2 top-0 bottom-0 w-px bg-[#36506f]" />
                      {group.items.map((post) => {
                        const status = getPrStatus(post);
                        const voteCount = post.extraSummary?.pr?.totalVoteCount ?? 0;
                        return (
                          <button
                            key={post.postId}
                            type="button"
                            onClick={() => navigate(`/community/pr/${post.postId}`)}
                            className="w-full text-left rounded-xl border border-[#334155] bg-[#111b2e] px-4 py-3.5 hover:border-[#60a5fa] transition-colors"
                          >
                            <p className="text-[17px] font-bold text-[#f8fbff]">{post.title}</p>
                            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-[#d7e4f6]">
                              <span className="font-semibold text-[#eff6ff]">{post.authorNickname || '알 수 없음'}</span>
                              <span>|</span>
                              <span>{formatDate(post.createdAt)}</span>
                              <span>|</span>
                              <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${getPrStatusBadgeClass(status)}`}>
                                {status}
                              </span>
                              <span className="text-[#c7d8ee]">리뷰 {voteCount}표</span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </section>
                ))}
              </div>
            )}
          </div>
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
              ) : posts.length === 0 ? (
                <div className="py-28 flex flex-col items-center justify-center">
                  <p className="font-semibold text-gray-400 text-[13px]">등록된 게시물이 없습니다.</p>
                  <p className="text-[12px] text-gray-300 mt-1">첫 번째 글을 작성해보세요.</p>
                </div>
              ) : (
                posts.map((post, idx) => (
                  <div
                    key={post.postId}
                    onClick={() =>
                      navigate(post.category === 'PR' ? `/community/pr/${post.postId}` : `/community/${post.postId}`)
                    }
                    className={`grid grid-cols-12 gap-3 py-3.5 text-[13.5px] items-center hover:bg-gray-50/60 transition-colors cursor-pointer group ${
                      idx !== posts.length - 1 ? 'border-b border-gray-50' : ''
                    }`}
                  >
                    <div className="col-span-1 flex items-center gap-0">
                      <span className={`w-1.5 h-1.5 rounded-full ${getCategoryDot(post.category)} flex-shrink-0`} />
                      <span className="text-[12px] text-gray-400 font-medium ml-1.5 hidden lg:inline">{getCategoryName(post.category)}</span>
                    </div>

                    <div className="col-span-7 flex items-center gap-2 min-w-0">
                      <span className="truncate text-gray-800 font-medium group-hover:text-gray-900">{post.title}</span>
                      {post.commentCount > 0 && (
                        <span className="text-[12px] font-semibold text-blue-500 shrink-0">[{post.commentCount}]</span>
                      )}
                    </div>

                    <div className="col-span-2 text-center text-gray-500 text-[13px] font-medium truncate">
                      {post.authorNickname || '알 수 없음'}
                    </div>

                    <div className="col-span-2 text-right text-gray-400 text-[12px] font-medium">{formatDate(post.createdAt)}</div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {!loading && totalPages > 1 && (
          <div className="mt-6 flex items-center justify-center gap-1.5">
            <button
              type="button"
              onClick={() => moveToListPage(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-2 rounded-lg border border-gray-100 text-[13px] font-medium text-gray-500 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              이전
            </button>

            {visiblePageNumbers.map((pageNumber) => (
              <button
                key={pageNumber}
                type="button"
                onClick={() => moveToListPage(pageNumber)}
                className={`min-w-[36px] h-[36px] rounded-lg text-[13px] font-semibold transition ${
                  pageNumber === currentPage ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-50'
                }`}
              >
                {pageNumber}
              </button>
            ))}

            <button
              type="button"
              onClick={() => moveToListPage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-2 rounded-lg border border-gray-100 text-[13px] font-medium text-gray-500 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              다음
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
