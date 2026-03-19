import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getPosts } from '../api/communityApi';
import type { BoardCategory, GetPostListResponseDto, PostSummaryDto } from '../types';

const PAGE_SIZE = 12;

const getCategoryName = (cat: BoardCategory | undefined) => {
  switch (cat) {
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

const getCategoryDot = (cat: BoardCategory | undefined) => {
  switch (cat) {
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

const formatRelativeDate = (dateStr: string) => {
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

const formatDeadline = (dateStr?: string) => {
  if (!dateStr) return '-';
  const parsed = new Date(dateStr);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('ko-KR', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
};

const formatPercent = (value: number) => `${Math.round(value)}%`;

const toWon = (value: number) =>
  new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);

const getDiscountRate = (originalPrice: number, dealPrice: number) => {
  if (!originalPrice || originalPrice <= 0) return 0;
  return Math.max(0, Math.round(((originalPrice - dealPrice) / originalPrice) * 100));
};

export const CommunityPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const category = searchParams.get('category') as BoardCategory | null;
  const pageParam = Number(searchParams.get('page'));
  const currentPage = Number.isInteger(pageParam) && pageParam >= 1 ? pageParam : 1;

  const [posts, setPosts] = useState<PostSummaryDto[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [pageInfo, setPageInfo] = useState<GetPostListResponseDto | null>(null);

  const isPollFeed = category === 'POLL';
  const isHotdealFeed = category === 'HOTDEAL';
  const isSpecialFeed = isPollFeed || isHotdealFeed;

  const categoryTitle = category ? `${getCategoryName(category)} 게시판` : '전체 게시글';

  const categoryDescription = useMemo(() => {
    if (category === 'COHORT') return '기수 게시판입니다. 자유롭게 의견을 나눠보세요.';
    if (category === 'POLL') return '토론 목록을 카드형으로 빠르게 살펴보세요.';
    if (category === 'HOTDEAL') return '핫딜 정보를 피드 형태로 확인해 보세요.';
    return '우리만의 소식을 나누고 함께 소통해 보세요.';
  }, [category]);

  useEffect(() => {
    const fetchPosts = async () => {
      setLoading(true);

      try {
        const res = await getPosts(category, undefined, currentPage - 1, PAGE_SIZE);
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

    fetchPosts();
  }, [category, currentPage]);

  const displayPosts = useMemo(() => {
    if (!isSpecialFeed) return posts;

    return [...posts].sort((a, b) => {
      if (isPollFeed) {
        const aClosed = a.extraSummary?.poll?.isClosed ? 1 : 0;
        const bClosed = b.extraSummary?.poll?.isClosed ? 1 : 0;
        if (aClosed !== bClosed) return aClosed - bClosed;
      }

      if (isHotdealFeed) {
        const aExpired = a.extraSummary?.hotdeal?.isExpired ? 1 : 0;
        const bExpired = b.extraSummary?.hotdeal?.isExpired ? 1 : 0;
        if (aExpired !== bExpired) return aExpired - bExpired;
      }

      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });
  }, [posts, isSpecialFeed, isPollFeed, isHotdealFeed]);

  const moveToListPage = (targetPage: number) => {
    const params = new URLSearchParams();

    if (category) params.set('category', category);
    if (targetPage > 1) params.set('page', String(targetPage));

    const queryString = params.toString();
    navigate(queryString ? `/community?${queryString}` : '/community');
  };

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

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
      <div className="px-7 pt-7 pb-5 flex justify-between items-start">
        <div>
          <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">{categoryTitle}</h1>
          <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
            {categoryDescription}
          </p>
        </div>

        <button
          type="button"
          onClick={() =>
            navigate(category ? `/community/write?category=${category}` : '/community/write')
          }
          className="inline-flex items-center gap-2 rounded-xl border border-blue-600 bg-blue-600 px-4 py-2.5 text-[14px] font-bold text-white shadow-sm transition hover:border-blue-700 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
        >
          <svg
            className="w-4 h-4 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <path d="M12 5v14M5 12h14" strokeLinecap="round" />
          </svg>
          <span>{isPollFeed ? '토론 작성' : isHotdealFeed ? '핫딜 작성' : '글쓰기'}</span>
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

        {!isSpecialFeed && (
          <div className="grid grid-cols-12 gap-3 py-3 text-[12px] font-semibold text-gray-300 uppercase tracking-wider items-center border-t border-gray-50">
            <div className="col-span-1">분류</div>
            <div className="col-span-7">제목</div>
            <div className="col-span-2 text-center">작성자</div>
            <div className="col-span-2 text-right pr-1">날짜</div>
          </div>
        )}

        <div className="flex flex-col flex-1">
          {loading ? (
            <div className="py-28 flex flex-col items-center justify-center">
              <div className="w-6 h-6 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
              <span className="text-[12px] text-gray-300 mt-3 font-medium">불러오는 중..</span>
            </div>
          ) : displayPosts.length === 0 ? (
            <div className="py-28 flex flex-col items-center justify-center">
              <p className="font-semibold text-gray-400 text-[13px]">등록된 게시물이 없습니다</p>
            </div>
          ) : isPollFeed ? (
            displayPosts.map((post, idx) => {
              const poll = post.extraSummary?.poll;
              const optionACount = poll?.optionACount ?? 0;
              const optionBCount = poll?.optionBCount ?? 0;
              const total = Math.max(1, optionACount + optionBCount);
              const optionARate = (optionACount / total) * 100;
              const optionBRate = (optionBCount / total) * 100;
              const isClosed = poll?.isClosed ?? false;

              return (
                <div
                  key={post.postId}
                  onClick={() => navigate(`/community/${post.postId}`)}
                  className={`py-4 cursor-pointer group ${
                    idx !== displayPosts.length - 1 ? 'border-b border-gray-50' : ''
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="text-[15px] font-semibold text-gray-900 group-hover:text-black truncate">
                      {post.title}
                    </h2>
                    <span
                      className={`shrink-0 rounded-full px-2 py-1 text-[11px] font-bold ${
                        isClosed ? 'bg-gray-100 text-gray-500' : 'bg-emerald-50 text-emerald-600'
                      }`}
                    >
                      {isClosed ? '마감' : '진행중'}
                    </span>
                  </div>

                  <p className="mt-1 text-[13px] text-gray-500 line-clamp-1">
                    {poll?.question ?? '토론 질문 미리보기를 불러오지 못했습니다.'}
                  </p>

                  <div className="mt-3 space-y-2">
                    <div>
                      <div className="mb-1 flex items-center justify-between text-[12px] text-gray-500 font-medium">
                        <span className="truncate">{poll?.optionA ?? '선택지 A'}</span>
                        <span>{formatPercent(optionARate)}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-gray-100">
                        <div
                          className="h-1.5 rounded-full bg-emerald-500"
                          style={{ width: `${optionARate}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="mb-1 flex items-center justify-between text-[12px] text-gray-500 font-medium">
                        <span className="truncate">{poll?.optionB ?? '선택지 B'}</span>
                        <span>{formatPercent(optionBRate)}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-gray-100">
                        <div
                          className="h-1.5 rounded-full bg-cyan-500"
                          style={{ width: `${optionBRate}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[12px] text-gray-400 font-medium">
                    <span>
                      투표 {poll?.totalVoteCount ?? optionACount + optionBCount}회 · 마감{' '}
                      {formatDeadline(poll?.deadlineAt)}
                    </span>
                    <span>{formatRelativeDate(post.createdAt)}</span>
                  </div>
                </div>
              );
            })
          ) : isHotdealFeed ? (
            displayPosts.map((post, idx) => {
              const hotdeal = post.extraSummary?.hotdeal;
              const dealPrice = hotdeal?.dealPriceAmount ?? 0;
              const originalPrice = hotdeal?.originalPriceAmount ?? 0;
              const discountRate = getDiscountRate(originalPrice, dealPrice);
              const isExpired = hotdeal?.isExpired ?? false;

              return (
                <div
                  key={post.postId}
                  onClick={() => navigate(`/community/${post.postId}`)}
                  className={`py-4 cursor-pointer group ${
                    idx !== displayPosts.length - 1 ? 'border-b border-gray-50' : ''
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="text-[15px] font-semibold text-gray-900 group-hover:text-black truncate">
                      {post.title}
                    </h2>
                    <span
                      className={`shrink-0 rounded-full px-2 py-1 text-[11px] font-bold ${
                        isExpired ? 'bg-gray-100 text-gray-500' : 'bg-rose-50 text-rose-600'
                      }`}
                    >
                      {isExpired ? '마감' : `${discountRate}% 할인`}
                    </span>
                  </div>

                  <div className="mt-2 flex items-end gap-2">
                    <strong className="text-[18px] font-bold text-gray-900">{toWon(dealPrice)}</strong>
                    {originalPrice > 0 && (
                      <span className="text-[13px] font-medium text-gray-400 line-through">
                        {toWon(originalPrice)}
                      </span>
                    )}
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[12px] text-gray-400 font-medium">
                    <span>
                      {hotdeal?.storeName ?? '-'} · 마감 {formatDeadline(hotdeal?.expiredAt)}
                    </span>
                    <span>{formatRelativeDate(post.createdAt)}</span>
                  </div>
                </div>
              );
            })
          ) : (
            displayPosts.map((post, idx) => (
              <div
                key={post.postId}
                onClick={() => navigate(`/community/${post.postId}`)}
                className={`grid grid-cols-12 gap-3 py-3.5 text-[13.5px] items-center hover:bg-gray-50/60 transition-colors cursor-pointer group ${
                  idx !== displayPosts.length - 1 ? 'border-b border-gray-50' : ''
                }`}
              >
                <div className="col-span-1 flex items-center gap-0">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${getCategoryDot(post.category)} flex-shrink-0`}
                  />
                  <span className="text-[12px] text-gray-400 font-medium ml-1.5 hidden lg:inline">
                    {getCategoryName(post.category)}
                  </span>
                </div>

                <div className="col-span-7 flex items-center gap-2 min-w-0">
                  <span className="truncate text-gray-800 font-medium group-hover:text-gray-900">
                    {post.title}
                  </span>

                  {post.commentCount > 0 && (
                    <span className="text-[12px] font-semibold text-blue-500 shrink-0">
                      [{post.commentCount}]
                    </span>
                  )}

                  {post.extraSummary?.poll && !post.extraSummary.poll.isClosed && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-500 font-semibold shrink-0">
                      진행중
                    </span>
                  )}
                </div>

                <div className="col-span-2 text-center text-gray-500 text-[13px] font-medium truncate">
                  {post.authorNickname || '알 수 없음'}
                </div>

                <div className="col-span-2 text-right text-gray-400 text-[12px] font-medium">
                  {formatRelativeDate(post.createdAt)}
                </div>
              </div>
            ))
          )}
        </div>

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
